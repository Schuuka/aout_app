import os
import csv
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

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
class DirMonitor(FileSystemEventHandler):
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
        print(f"données mises à jour dans {self.csv_path}")

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
        print(message)
        log_event(message)

if __name__ == "__main__":
    directory = r'C:\Users\tonyt\OneDrive\Bureau\trucs\observation'
    metadata = scan_dir(directory)
    csv_path = r'C:\Users\tonyt\OneDrive - EPHEC asbl\2324\devII\aout_app\metadata.csv'
    write_csv(metadata, csv_path)
    print(f"données écrites dans {csv_path}")

    event_handler = DirMonitor(directory, csv_path)
    observer = Observer()
    observer.schedule(event_handler, path=directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()