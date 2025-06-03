import customtkinter as ctk
import random

class DemineurApp(ctk.CTk):
    def __init__(self, largeur=8, hauteur=8, mines=10):
        super().__init__()
        
        # Configuration de la fenêtre
        self.title("Démineur")
        self.geometry("500x500")
        ctk.set_appearance_mode("dark")
        
        # Paramètres du jeu
        self.largeur = largeur
        self.hauteur = hauteur
        self.mines = mines
        self.grille = []
        self.boutons = []
        self.partie_en_cours = True
        
        # Création de l'interface
        self.creer_interface()
        self.nouvelle_partie()
        
    def creer_interface(self):
        # Frame pour les boutons
        self.frame_jeu = ctk.CTkFrame(self)
        self.frame_jeu.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Bouton pour recommencer
        self.btn_rejouer = ctk.CTkButton(self, text="Nouvelle partie", command=self.nouvelle_partie)
        self.btn_rejouer.pack(pady=10)
        
    def nouvelle_partie(self):
        # Réinitialiser la partie
        self.partie_en_cours = True
        
        # Effacer les anciens boutons
        for widget in self.frame_jeu.winfo_children():
            widget.destroy()
        
        # Initialiser la grille
        self.grille = [[0 for _ in range(self.largeur)] for _ in range(self.hauteur)]
        self.decouvert = [[False for _ in range(self.largeur)] for _ in range(self.hauteur)]
        self.drapeaux = [[False for _ in range(self.largeur)] for _ in range(self.hauteur)]
        
        # Placer les mines
        self.placer_mines()
        self.calculer_voisins()
        
        # Créer les boutons
        self.boutons = []
        for y in range(self.hauteur):
            ligne_boutons = []
            for x in range(self.largeur):
                btn = ctk.CTkButton(
                    self.frame_jeu, 
                    text="", 
                    width=30, 
                    height=30,
                    command=lambda x=x, y=y: self.cliquer_case(x, y)
                )
                btn.bind("<Button-3>", lambda event, x=x, y=y: self.placer_drapeau(x, y))
                btn.grid(row=y, column=x, padx=1, pady=1)
                ligne_boutons.append(btn)
            self.boutons.append(ligne_boutons)
    
    def placer_mines(self):
        mines_placees = 0
        while mines_placees < self.mines:
            x = random.randint(0, self.largeur - 1)
            y = random.randint(0, self.hauteur - 1)
            if self.grille[y][x] != -1:
                self.grille[y][x] = -1
                mines_placees += 1
    
    def calculer_voisins(self):
        for y in range(self.hauteur):
            for x in range(self.largeur):
                if self.grille[y][x] == -1:
                    continue
                compteur = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.largeur and 0 <= ny < self.hauteur:
                            if self.grille[ny][nx] == -1:
                                compteur += 1
                self.grille[y][x] = compteur
    
    def cliquer_case(self, x, y):
        if not self.partie_en_cours or self.decouvert[y][x] or self.drapeaux[y][x]:
            return
        
        self.decouvert[y][x] = True
        self.mettre_a_jour_affichage()
        
        if self.grille[y][x] == -1:
            self.partie_en_cours = False
            self.reveler_mines()
            self.showinfo("Perdu", "Vous avez cliqué sur une mine !")
        elif self.grille[y][x] == 0:
            self.decouvrir_zone_vide(x, y)
        
        if self.verifier_victoire():
            self.partie_en_cours = False
            self.showinfo("Gagné", "Félicitations, vous avez gagné !")
    
    def placer_drapeau(self, x, y):
        if not self.partie_en_cours or self.decouvert[y][x]:
            return
        
        self.drapeaux[y][x] = not self.drapeaux[y][x]
        self.mettre_a_jour_affichage()
    
    def decouvrir_zone_vide(self, x, y):
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < self.largeur and 0 <= ny < self.hauteur:
                    if not self.decouvert[ny][nx] and not self.drapeaux[ny][nx]:
                        self.decouvert[ny][nx] = True
                        if self.grille[ny][nx] == 0:
                            self.decouvrir_zone_vide(nx, ny)
        self.mettre_a_jour_affichage()
    
    def reveler_mines(self):
        for y in range(self.hauteur):
            for x in range(self.largeur):
                if self.grille[y][x] == -1:
                    self.decouvert[y][x] = True
        self.mettre_a_jour_affichage()
    
    def mettre_a_jour_affichage(self):
        for y in range(self.hauteur):
            for x in range(self.largeur):
                if self.drapeaux[y][x]:
                    self.boutons[y][x].configure(text="🚩", fg_color="orange")
                elif not self.decouvert[y][x]:
                    self.boutons[y][x].configure(text="", fg_color="#1a1a1a")
                else:
                    if self.grille[y][x] == -1:
                        self.boutons[y][x].configure(text="💣", fg_color="red")
                    elif self.grille[y][x] > 0:
                        couleurs = ["", "blue", "green", "red", "purple", "maroon", "cyan", "black", "gray"]
                        self.boutons[y][x].configure(
                            text=str(self.grille[y][x]), 
                            fg_color="#333333",
                            text_color=couleurs[self.grille[y][x]]
                        )
                    else:
                        self.boutons[y][x].configure(text="", fg_color="#333333")
    
    def verifier_victoire(self):
        for y in range(self.hauteur):
            for x in range(self.largeur):
                if self.grille[y][x] != -1 and not self.decouvert[y][x]:
                    return False
        return True
    
    def showinfo(self, title, message):
        top = ctk.CTkToplevel(self)
        top.title(title)
        top.geometry("300x100")
        
        label = ctk.CTkLabel(top, text=message)
        label.pack(pady=20)
        
        btn = ctk.CTkButton(top, text="OK", command=top.destroy)
        btn.pack(pady=10)

# Lancer l'application
if __name__ == "__main__":
    app = DemineurApp(largeur=8, hauteur=8, mines=10)
    app.mainloop()