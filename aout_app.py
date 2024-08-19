import os
import csv
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import argparse
import cmd

# Extraire les métadonnées d'un fichier
def get_metadata(file_path):
    """
    Extrait les métadonnées d'un fichier.

    PRE:
    - `file_path` est une chaîne représentant le chemin du fichier.

    POST:
    - Retourne un dictionnaire contenant les métadonnées du fichier.
    """
    stat = os.stat(file_path)
    return {
        'name': os.path.basename(file_path),
        'creation_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modification_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'size': stat.st_size
    }

# Parcourir un répertoire et extraire les métadonnées des fichiers
def scan_dir(directory):
    """
    Parcourt un répertoire et extrait les métadonnées des fichiers.

    PRE:
    - `directory` est une chaîne représentant le chemin du répertoire.

    POST:
    - Retourne une liste contenant les métadonnées des fichiers.
    """
    metadata = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            metadata.append(get_metadata(file_path))
    return metadata

# Écrire les métadonnées dans un fichier CSV
def write_csv(metadata, csv_path):
    """
    Écrit les métadonnées dans un fichier CSV.

    PRE:
    - `metadata` est une liste de dictionnaires contenant les métadonnées des fichiers.
    - `csv_path` est une chaîne représentant le chemin du fichier CSV.

    POST:
    - Les métadonnées sont écrites dans le fichier CSV.
    """
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['name', 'creation_time', 'modification_time', 'size']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for data in metadata:
            writer.writerow(data)

# Journaliser les événements
def log_event(message):
    """
    Journalise un événement dans un fichier de log.

    PRE:
    - `message` est une chaîne représentant le message à journaliser.

    POST:
    - Le message est ajouté au fichier de log avec un horodatage.
    """
    with open("event_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

class ModException(Exception):
    pass

# Gestionnaire d'événements pour watchdog
class Monitor(FileSystemEventHandler):
    def __init__(self, directory, csv_path):
        """
        Initialise un gestionnaire d'événements pour surveiller un répertoire.
        
        PRE:
        - `directory`: chemin du répertoire à surveiller.
        - `csv_path`: chemin du fichier CSV pour stocker les métadonnées.
        
        POST:
        - Gestionnaire d'événements initialisé pour surveiller les modifications dans le répertoire.
        """
        self._directory = directory
        self._csv_path = csv_path
        self._recent_mods = {}
        self._recent_creations = {}

    def on_modified(self, event):
        """
        Gère les événements de modification de fichier.

        PRE:
        - `event` est un événement de modification de fichier.

        POST:
        - Les métadonnées sont mises à jour si le fichier a été modifié.

        #Exception: ModException
        # Gestion de l'exception ModException
        # Si une modification est détectée trop rapidement après une création ou une autre modification,
        # l'exception est levée et l'événement est ignoré.
        """
        if not event.is_directory:
            try:
                self.log_event_type(event.src_path, "modification")
                self.update_metadata()
            except ModException:
                pass

    def on_created(self, event):
        """
        Gère les événements de création de fichier.

        PRE:
        - `event` est un événement de création de fichier.

        POST:
        - Les métadonnées sont mises à jour si un fichier a été créé.
        """
        if not event.is_directory:
            self.log_event_type(event.src_path, "creation")
            self.update_metadata()

    def on_deleted(self, event):
        """
        Gère les événements de suppression de fichier.

        PRE:
        - `event` est un événement de suppression de fichier.

        POST:
        - Les métadonnées sont mises à jour si un fichier a été supprimé.
        """
        if not event.is_directory:
            self.log_event_type(event.src_path, "suppression")
            self.update_metadata()

    def update_metadata(self):
        """
        Met à jour les métadonnées des fichiers dans le répertoire surveillé.

        PRE:
        - Le répertoire surveillé contient des fichiers.

        POST:
        - Les métadonnées des fichiers sont mises à jour dans le fichier CSV.
        """
        metadata = scan_dir(self._directory)
        write_csv(metadata, self._csv_path)
        print(f"Données à jour dans le csv")

    def log_event_type(self, file_path, event_type):
        """
        Journalise le type d'événement pour un fichier.

        PRE:
        - `file_path` est une chaîne représentant le chemin du fichier.
        - `event_type` est une chaîne représentant le type d'événement (modification, création, suppression).

        POST:
        - L'événement est journalisé avec un horodatage.
        """
        current_time = time.time()
        if event_type == "modification":
            if file_path in self._recent_creations and current_time - self._recent_creations[file_path] <= 2:
                raise ModException()
            if file_path in self._recent_mods and current_time - self._recent_mods[file_path] <= 2:
                raise ModException()
            self._recent_mods[file_path] = current_time
        elif event_type == "creation":
            self._recent_creations[file_path] = current_time
        message = f"{event_type} du fichier: {os.path.basename(file_path)}"
        log_event(message)

class Shell(cmd.Cmd):
    intro = "\nCréation ou suppression de fichier dans le directory. 'help' pour les commandes.\n\n"
    prompt = "--> "

    def __init__(self, directory, csv_path):
        """
        Initialise une instance de Shell pour gérer les commandes de création et suppression de fichiers.

        PRE:
        - `directory` est une chaîne représentant le chemin du répertoire à surveiller.
        - `csv_path` est une chaîne représentant le chemin du fichier CSV pour stocker les métadonnées.

        POST:
        - Une instance de Shell est initialisée pour gérer les commandes.
        """
        super().__init__()
        self._directory = directory
        self._csv_path = csv_path

    def pre_create(self, file_path):
        if os.path.exists(file_path):
            print(f"Erreur: Le fichier {os.path.basename(file_path)} existe déjà.")
            return False
        return True

    def post_create(self, file_path):
        print(f"Fichier créé: {os.path.basename(file_path)}")

    def pre_delete(self, file_path):
        if not os.path.exists(file_path):
            print(f"Erreur: Le fichier {os.path.basename(file_path)} n'existe pas.")
            return False
        return True

    def post_delete(self, file_path):
        print(f"Fichier supprimé: {os.path.basename(file_path)}")

    def do_create(self, arg):
        """
        Crée un fichier.

        PRE:
        - `arg` est une chaîne représentant le nom du fichier à créer.

        POST:
        - Le fichier est créé si les préconditions sont remplies.
        """
        file_path = os.path.join(self._directory, arg)
        if self.pre_create(file_path):
            with open(file_path, 'w') as f:
                f.write('')
            self.post_create(file_path)

    def do_delete(self, arg):
        """
        Supprime un fichier.

        PRE:
        - `arg` est une chaîne représentant le nom du fichier à supprimer.

        POST:
        - Le fichier est supprimé si les préconditions sont remplies.
        """
        file_path = os.path.join(self._directory, arg)
        if self.pre_delete(file_path):
            os.remove(file_path)
            self.post_delete(file_path)

    def do_exit(self, arg):
        """
        Quitte l'application.

        PRE:
        - Aucune.

        POST:
        - L'application est terminée.
        """
        print("=====================================")
        return True

class FileWriter(Shell):
    def do_create(self, arg):
        """
        Crée un fichier avec contenu.

        PRE:
        - `arg` est une chaîne représentant le nom du fichier et le contenu à écrire.

        POST:
        - Le fichier est créé avec le contenu spécifié si les préconditions sont remplies.
        """
        parts = arg.split(' ', 1)
        if len(parts) == 2:
            file_name, content = parts
        else:
            file_name = parts[0]
            content = ""
        file_path = os.path.join(self._directory, file_name)
        if self.pre_create(file_path):
            with open(file_path, 'w') as f:
                f.write(content)
            self.post_create(file_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Surveille un répertoire et met à jour un fichier CSV avec les données des fichiers.")
    parser.add_argument("--directory", help="Le répertoire à surveiller", default=r'C:\Users\tonyt\OneDrive\Bureau\trucs\observation')
    parser.add_argument("--csv_path", help="Le chemin du fichier CSV pour stocker les données", default=r'C:\Users\tonyt\OneDrive - EPHEC asbl\2324\devII\aout_app\metadata.csv')

    args = parser.parse_args()

    directory = args.directory
    metadata = scan_dir(directory)
    csv_path = args.csv_path
    write_csv(metadata, csv_path)

    event_handler = Monitor(directory, csv_path)
    observer = Observer()
    observer.schedule(event_handler, path=directory, recursive=True)
    observer.start()

    shell = FileWriter(directory, csv_path)
    shell.cmdloop()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()