import cv2
import numpy as np
import pytesseract
import time
import pyautogui
from PIL import ImageGrab, Image
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from functools import partial
from random import randint, randrange
import sys
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

# Configuration
sys.setrecursionlimit(100_000)
pytesseract.pytesseract.tesseract_cmd = r"C:\Users\anatolemorice\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
NB_ITER = 0
NB_BONOBO = 0
PILE = []

class ScreenCapture:
    def __init__(self):
        self.root = tk.Tk()
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-alpha', 0.3)
        self.root.configure(bg='white')
        
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        
        self.canvas = tk.Canvas(self.root, cursor="cross", bg='grey11', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        
        self.selection_complete = False
        self.rect = None
        
        self.root.mainloop()
    
    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(0, 0, 0, 0, outline='red', width=2)
    
    def on_drag(self, event):
        self.end_x, self.end_y = event.x, event.y
        self.canvas.coords(self.rect, self.start_x, self.start_y, self.end_x, self.end_y)
    
    def on_release(self, event):
        self.end_x, self.end_y = event.x, event.y
        self.selection_complete = True
        self.root.quit()
        self.root.destroy()
    
    def get_selection(self):
        if self.selection_complete:
            x1, y1, x2, y2 = self.start_x, self.start_y, self.end_x, self.end_y
            if x1 > x2:
                x1, x2 = x2, x1
            if y1 > y2:
                y1, y2 = y2, y1
            return (x1, y1, x2-x1, y2-y1)
        return None

class DemineurSolver:
    def __init__(self, hauteur=9, largeur=9):
        self.hauteur = hauteur
        self.largeur = largeur
        self.grille = np.zeros((hauteur, largeur), dtype=np.int8) - 1  # -1 = inconnu
        self.bombes_decouvertes = set()
        self.drapeaux = set()
    
    def update_grid(self, new_grid):
        """Met à jour la grille avec les nouvelles informations"""
        for i in range(self.hauteur):
            for j in range(self.largeur):
                if new_grid[i][j] != -1 and self.grille[i][j] == -1:
                    self.grille[i][j] = new_grid[i][j]
    
    def get_unknown_cells(self):
        """Retourne les cellules encore inconnues"""
        return [(i, j) for i in range(self.hauteur) for j in range(self.largeur) if self.grille[i][j] == -1 and (i, j) not in self.drapeaux]
    
    def get_adjacent_unknowns(self, i, j):
        """Retourne les cellules inconnues adjacentes"""
        unknowns = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if (dx != 0 or dy != 0) and 0 <= i + dy < self.hauteur and 0 <= j + dx < self.largeur:
                    if self.grille[i + dy][j + dx] == -1 and (i + dy, j + dx) not in self.drapeaux:
                        unknowns.append((i + dy, j + dx))
        return unknowns
    
    def get_adjacent_flags(self, i, j):
        """Compte les drapeaux adjacents"""
        count = 0
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if (dx != 0 or dy != 0) and 0 <= i + dy < self.hauteur and 0 <= j + dx < self.largeur:
                    if (i + dy, j + dx) in self.drapeaux:
                        count += 1
        return count
    
    def find_safe_moves(self):
        """Trouve les coups sûrs en utilisant la logique du démineur"""
        safe_moves = []
        flag_moves = []
        
        # D'abord vérifier les cases numérotées
        for i in range(self.hauteur):
            for j in range(self.largeur):
                if self.grille[i][j] > 0:
                    unknowns = self.get_adjacent_unknowns(i, j)
                    flags = self.get_adjacent_flags(i, j)
                    
                    # Si nombre de drapeaux adjacents == nombre sur la case
                    # Alors toutes les autres inconnues sont sûres
                    if flags == self.grille[i][j] and unknowns:
                        safe_moves.extend(unknowns)
                    
                    # Si nombre d'inconnues + drapeaux == nombre sur la case
                    # Alors toutes les inconnues sont des bombes
                    elif len(unknowns) + flags == self.grille[i][j] and unknowns:
                        flag_moves.extend(unknowns)
        
        # Éliminer les doublons
        safe_moves = list(set(safe_moves))
        flag_moves = list(set(flag_moves))
        
        return safe_moves, flag_moves
    
    def make_move(self):
        """Détermine le prochain coup à jouer"""
        safe_moves, flag_moves = self.find_safe_moves()
        
        # D'abord placer les drapeaux évidents
        if flag_moves:
            return flag_moves[0][0], flag_moves[0][1], True
        
        # Ensuite les coups sûrs évidents
        if safe_moves:
            return safe_moves[0][0], safe_moves[0][1], False
        
        # Sinon choisir au hasard parmi les cases non découvertes
        unknowns = self.get_unknown_cells()
        if unknowns:
            return unknowns[0][0], unknowns[0][1], False
        
        return None

def recognize_grid(selection_area):
    """Reconnaît la grille actuelle du démineur à partir de la capture d'écran"""
    x, y, w, h = selection_area
    screenshot = ImageGrab.grab(bbox=(x, y, x+w, y+h))
    
    # Traitement de l'image
    img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)
    thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
    
    # Détection de la grille
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    
    max_contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(max_contour)
    grid = thresh[y:y+h, x:x+w]
    
    # Découpage en cellules
    cell_height = h // 9
    cell_width = w // 9
    
    current_grid = [[-1 for _ in range(9)] for _ in range(9)]
    
    for i in range(9):
        for j in range(9):
            cell = grid[i*cell_height:(i+1)*cell_height, j*cell_width:(j+1)*cell_width]
            cell = cv2.resize(cell, (50, 50))
            
            # Reconnaissance du chiffre
            config = '--psm 10 --oem 3 -c tessedit_char_whitelist=012345678'
            digit = pytesseract.image_to_string(cell, config=config)
            
            if digit.strip():
                current_grid[i][j] = int(digit[0])
    
    return current_grid

class DemineurApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Démineur Solver AI")
        self.root.geometry("500x400")
        
        self.selection_area = None
        self.solver = None
        
        self.create_widgets()
        
    def create_widgets(self):
        ctk.CTkLabel(self.root, text="Démineur Solver AI", font=("Arial", 20)).pack(pady=20)
        
        self.info_label = ctk.CTkLabel(self.root, text="1. Sélectionnez la zone du démineur avec votre souris")
        self.info_label.pack(pady=10)
        
        self.capture_btn = ctk.CTkButton(self.root, text="Capturer la zone", command=self.start_area_selection)
        self.capture_btn.pack(pady=10)
        
        self.solve_btn = ctk.CTkButton(self.root, text="Résoudre le Démineur", command=self.solve_demineur, state="disabled")
        self.solve_btn.pack(pady=20)
        
        self.preview_label = ctk.CTkLabel(self.root, text="Aperçu de la grille détectée:")
        self.preview_label.pack()
        
        self.grid_text = tk.Text(self.root, height=9, width=21, font=("Courier", 16))
        self.grid_text.pack(pady=10)
        
    def start_area_selection(self):
        self.root.withdraw()
        time.sleep(1)
        messagebox.showinfo("Instructions", "Sélectionnez la zone du démineur avec votre souris (glisser-déposer)")
        
        sc = ScreenCapture()
        self.selection_area = sc.get_selection()
        
        self.root.deiconify()
        if self.selection_area:
            self.initialize_solver()
    
    def initialize_solver(self):
        # Initialiser le solver
        self.solver = DemineurSolver(9, 9)
        
        # Première reconnaissance
        current_grid = recognize_grid(self.selection_area)
        if current_grid:
            self.solver.update_grid(current_grid)
            self.display_grid(current_grid)
            self.solve_btn.configure(state="normal")
        else:
            messagebox.showerror("Erreur", "Impossible de reconnaître la grille")
    
    def display_grid(self, grid):
        self.grid_text.delete(1.0, tk.END)
        for row in grid:
            line = " ".join(str(x) if x != -1 else "." for x in row)
            self.grid_text.insert(tk.END, line + "\n")
    
    def solve_demineur(self):
        if not self.selection_area or not self.solver:
            return
        
        while True:
            # Faire un mouvement
            move = self.solver.make_move()
            if not move:
                messagebox.showinfo("Terminé", "Partie terminée!")
                break
            
            i, j, is_flag = move
            x, y, w, h = self.selection_area
            cell_width = w // 9
            cell_height = h // 9
            
            # Calculer la position du centre de la cellule
            center_x = x + (j * cell_width) + (cell_width // 2)
            center_y = y + (i * cell_height) + (cell_height // 2)
            
            # Effectuer l'action
            pyautogui.click(center_x, center_y, button='right' if is_flag else 'left')
            
            if is_flag:
                self.solver.drapeaux.add((i, j))
            else:
                # Attendre que le jeu réagisse
                time.sleep(0.5)
                
                # Prendre une nouvelle capture et mettre à jour la grille
                current_grid = recognize_grid(self.selection_area)
                if current_grid:
                    self.solver.update_grid(current_grid)
                    self.display_grid(current_grid)
                    self.root.update()  # Mettre à jour l'interface
                else:
                    messagebox.showerror("Erreur", "Impossible de reconnaître la grille après le coup")
                    break
            
            # Petite pause entre les actions
            time.sleep(0.3)

if __name__ == "__main__":
    app = DemineurApp()
    app.root.mainloop()