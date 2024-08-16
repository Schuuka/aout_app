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
    stat = os.stat(file_path)
    return {
        'name': os.path.basename(file_path),
        'creation_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modification_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'size': stat.st_size
    }

# Parcourir un répertoire et extraire les métadonnées des fichiers
def scan_dir(directory):
    metadata = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            metadata.append(get_metadata(file_path))
    return metadata

# Écrire les métadonnées dans un fichier CSV
def write_csv(metadata, csv_path):
    with open(csv_path, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['name', 'creation_time', 'modification_time', 'size']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for data in metadata:
            writer.writerow(data)

# Journaliser les événements
def log_event(message):
    with open("event_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

class ModException(Exception):
    pass

# Gestionnaire d'événements pour watchdog
class Monitor(FileSystemEventHandler):
    def __init__(self, directory, csv_path):
        self.directory = directory
        self.csv_path = csv_path
        self.recent_mods = {}
        self.recent_creations = {}

    def on_modified(self, event):
        if not event.is_directory:
            try:
                self.log_event_type(event.src_path, "modification")
                self.update_metadata()
            except ModException:
                pass

    def on_created(self, event):
        if not event.is_directory:
            self.log_event_type(event.src_path, "creation")
            self.update_metadata()

    def on_deleted(self, event):
        if not event.is_directory:
            self.log_event_type(event.src_path, "suppression")
            self.update_metadata()

    def update_metadata(self):
        metadata = scan_dir(self.directory)
        write_csv(metadata, self.csv_path)
        print(f"Données à jour dans le csv")

    def log_event_type(self, file_path, event_type):
        current_time = time.time()
        if event_type == "modification":
            if file_path in self.recent_creations and current_time - self.recent_creations[file_path] <= 2:
                raise ModException()
            if file_path in self.recent_mods and current_time - self.recent_mods[file_path] <= 2:
                raise ModException()
            self.recent_mods[file_path] = current_time
        elif event_type == "creation":
            self.recent_creations[file_path] = current_time
        message = f"{event_type} du fichier: {os.path.basename(file_path)}"
        log_event(message)

class Shell(cmd.Cmd):
    intro = "\nCréation ou suppression de fichier dans le directory. 'help' pour les commandes.\n\n"
    prompt = "--> "

    def __init__(self, directory, csv_path):
        super().__init__()
        self.directory = directory
        self.csv_path = csv_path

    def do_create(self, arg):
        "Créer un fichier: create <nom_du_fichier>"
        file_path = os.path.join(self.directory, arg)
        with open(file_path, 'w') as f:
            f.write('')
        print(f"Fichier créé: {os.path.basename(file_path)}")

    def do_delete(self, arg):
        "Supprimer un fichier: delete <nom_du_fichier>"
        file_path = os.path.join(self.directory, arg)
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"Fichier supprimé: {os.path.basename(file_path)}")
        else:
            print(f"Fichier non trouvé: {os.path.basename(file_path)}")

    def do_exit(self, arg):
        "Quitter l'app"
        print("=====================================")
        return True

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

    shell = Shell(directory, csv_path)
    shell.cmdloop()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()