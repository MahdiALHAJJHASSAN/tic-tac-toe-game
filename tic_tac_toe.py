import tkinter as tk
from tkinter import messagebox, simpledialog
import random
import requests


class TicTacToe:
    def __init__(self, root):
        self.window = root
        self.window.title("TIC-TAC-TOE - Jeu Connecté")
        self.window.configure(bg='#2C3E50')
        self.window.resizable(False, False)

        self.players = ["X", "O"]
        self.current_player = random.choice(self.players)
        self.game_btns = [[None, None, None] for _ in range(3)]
        self.game_active = True
        self.base_url = "http://127.0.0.1:5000"

        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur"""
        # Titre
        self.title_label = tk.Label(
            self.window,
            text="TIC-TAC-TOE",
            font=('Arial', 24, 'bold'),
            fg='#ECF0F1',
            bg='#2C3E50'
        )
        self.title_label.pack(pady=10)

        # Label du tour
        self.turn_label = tk.Label(
            self.window,
            text=f"Joueur {self.current_player} commence!",
            font=('Arial', 16),
            fg='#ECF0F1',
            bg='#2C3E50'
        )
        self.turn_label.pack(pady=5)

        # Frame des boutons
        self.btns_frame = tk.Frame(self.window, bg='#2C3E50')
        self.btns_frame.pack(pady=20)

        # Création des boutons du jeu
        for row in range(3):
            for col in range(3):
                btn = tk.Button(
                    self.btns_frame,
                    text="",
                    font=('Arial', 20, 'bold'),
                    width=6,
                    height=3,
                    bg='#34495E',
                    fg='#ECF0F1',
                    relief='raised',
                    bd=3,
                    command=lambda r=row, c=col: self.next_turn(r, c)
                )
                btn.grid(row=row, column=col, padx=5, pady=5)
                self.game_btns[row][col] = btn

        # Frame des contrôles
        control_frame = tk.Frame(self.window, bg='#2C3E50')
        control_frame.pack(pady=20)

        # Bouton restart
        self.restart_btn = tk.Button(
            control_frame,
            text="Nouvelle Partie",
            font=('Arial', 14),
            bg='#E74C3C',
            fg='white',
            command=self.start_new_game
        )
        self.restart_btn.pack(side=tk.LEFT, padx=10)

        # Bouton quitter
        self.quit_btn = tk.Button(
            control_frame,
            text="Quitter",
            font=('Arial', 14),
            bg='#95A5A6',
            fg='white',
            command=self.window.quit
        )
        self.quit_btn.pack(side=tk.LEFT, padx=10)

        # Label score
        self.score_label = tk.Label(
            control_frame,
            text="Gagnez pour gagner des points!",
            font=('Arial', 12),
            fg='#F1C40F',
            bg='#2C3E50'
        )
        self.score_label.pack(side=tk.LEFT, padx=20)

    def next_turn(self, row, col):
        """Gère le tour du joueur"""
        if not self.game_active or self.game_btns[row][col]['text'] != "":
            return

        self.game_btns[row][col]['text'] = self.current_player

        if self.check_winner():
            self.turn_label.config(text=f"Joueur {self.current_player} gagne!")
            self.highlight_winning_cells()
            self.game_active = False
            self.update_score(10, f"Victoire de {self.current_player}!")
            messagebox.showinfo("Félicitations!", f"Joueur {self.current_player} a gagné!\n+10 points!")
        elif not self.check_empty_spaces():
            self.turn_label.config(text="Match nul!")
            self.highlight_tie()
            self.game_active = False
            self.update_score(5, "Match nul!")
            messagebox.showinfo("Match nul", "Aucun gagnant!\n+5 points!")
        else:
            self.current_player = self.players[1] if self.current_player == self.players[0] else self.players[0]
            self.turn_label.config(text=f"Tour du joueur {self.current_player}")

    def check_winner(self):
        """Vérifie s'il y a un gagnant"""
        # Vérification des lignes
        for row in range(3):
            if self.game_btns[row][0]['text'] == self.game_btns[row][1]['text'] == self.game_btns[row][2]['text'] != "":
                return True

        # Vérification des colonnes
        for col in range(3):
            if self.game_btns[0][col]['text'] == self.game_btns[1][col]['text'] == self.game_btns[2][col]['text'] != "":
                return True

        # Vérification des diagonales
        if self.game_btns[0][0]['text'] == self.game_btns[1][1]['text'] == self.game_btns[2][2]['text'] != "":
            return True
        if self.game_btns[0][2]['text'] == self.game_btns[1][1]['text'] == self.game_btns[2][0]['text'] != "":
            return True

        return False

    def highlight_winning_cells(self):
        """Met en évidence les cellules gagnantes"""
        # Vérification des lignes
        for row in range(3):
            if self.game_btns[row][0]['text'] == self.game_btns[row][1]['text'] == self.game_btns[row][2]['text'] != "":
                for col in range(3):
                    self.game_btns[row][col].config(bg='#27AE60', fg='white')
                return

        # Vérification des colonnes
        for col in range(3):
            if self.game_btns[0][col]['text'] == self.game_btns[1][col]['text'] == self.game_btns[2][col]['text'] != "":
                for row in range(3):
                    self.game_btns[row][col].config(bg='#27AE60', fg='white')
                return

        # Vérification des diagonales
        if self.game_btns[0][0]['text'] == self.game_btns[1][1]['text'] == self.game_btns[2][2]['text'] != "":
            for i in range(3):
                self.game_btns[i][i].config(bg='#27AE60', fg='white')
            return
        if self.game_btns[0][2]['text'] == self.game_btns[1][1]['text'] == self.game_btns[2][0]['text'] != "":
            for i in range(3):
                self.game_btns[i][2 - i].config(bg='#27AE60', fg='white')

    def highlight_tie(self):
        """Met en évidence le match nul"""
        for row in range(3):
            for col in range(3):
                self.game_btns[row][col].config(bg='#F39C12', fg='white')

    def check_empty_spaces(self):
        """Vérifie s'il reste des cases vides"""
        for row in range(3):
            for col in range(3):
                if self.game_btns[row][col]['text'] == "":
                    return True
        return False

    def start_new_game(self):
        """Démarre une nouvelle partie"""
        for row in range(3):
            for col in range(3):
                self.game_btns[row][col].config(
                    text="",
                    bg='#34495E',
                    fg='#ECF0F1'
                )

        self.current_player = random.choice(self.players)
        self.turn_label.config(text=f"Joueur {self.current_player} commence!")
        self.game_active = True

    def update_score(self, points, message):
        """Met à jour le score sur le serveur"""
        try:
            username = simpledialog.askstring("Sauvegarde du score",
                                              "Entrez votre nom d'utilisateur pour sauvegarder votre score:")

            if username:
                response = requests.post(
                    f"{self.base_url}/update-score",
                    json={'username': username, 'score': points}
                )

                if response.status_code == 200:
                    result = response.json()
                    if result['success']:
                        messagebox.showinfo("Score sauvegardé",
                                            f"{message}\nNouveau score: {result['new_score']} points")
                    else:
                        messagebox.showerror("Erreur", f"Erreur: {result.get('error', 'Inconnue')}")
                else:
                    messagebox.showerror("Erreur", "Impossible de se connecter au serveur")
            else:
                messagebox.showwarning("Score non sauvegardé", "Score non sauvegardé (nom d'utilisateur manquant)")

        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de sauvegarder le score: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    game = TicTacToe(root)
    root.mainloop()