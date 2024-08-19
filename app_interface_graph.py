import tkinter as tk
from tkinter import messagebox

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Interface Graphique")
        self.geometry("400x300")
        
        self.label = tk.Label(self, text="Ferme d'animaux")
        self.label.pack(pady=20)

        self.entry = tk.Entry(self)
        self.entry.pack(pady=10)
        
        self.button = tk.Button(self, text="Ajouter un animal", command=self.on_button_click)
        self.button.pack(pady=10)
    
    def on_button_click(self):
        """
        Pré:
        - L'utilisateur doit avoir saisi un nom d'animal dans le champ d'entrée.
        - Le champ d'entrée ne doit pas être vide.

        Post:
        - Si le champ d'entrée contient un texte, le label affiche le nom de l'animal ajouté.
        - Une boîte d'information s'affiche pour confirmer.
        - Si le champ d'entrée est vide, une boîte d'avertissement s'affiche pour redemander un nom correct.
        """
        animal_name = self.entry.get()
        if animal_name:
            self.label.config(text=f"Animal ajouté: {animal_name}")
            messagebox.showinfo("Super", f"Un animal a été ajouté: {animal_name}")
        else:
            messagebox.showwarning("Attention", "Veuillez entrer le nom d'un animal.")

if __name__ == "__main__":
    app = App()
    app.mainloop()