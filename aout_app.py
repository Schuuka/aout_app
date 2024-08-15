import os
import csv
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
import threading

# Fonction pour extraire les métadonnées d'un fichier
def get_file_metadata(file_path):
    stat = os.stat(file_path)
    return {
        'name': os.path.basename(file_path),
        'creation_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modification_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
        'size': stat.st_size
    }

# Fonction pour parcourir un répertoire et extraire les métadonnées des fichiers
def scan_directory(directory):
    metadata_list = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            metadata = get_file_metadata(file_path)
            metadata_list.append(metadata)
    return metadata_list

# Fonction pour écrire les métadonnées dans un fichier CSV
def write_metadata_to_csv(metadata_list, csv_file_path):
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        fieldnames = ['name', 'creation_time', 'modification_time', 'size']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for metadata in metadata_list:
            writer.writerow(metadata)

# Classe de gestionnaire d'événements pour watchdog
class MetadataEventHandler(FileSystemEventHandler):
    def __init__(self, directory, csv_file_path):
        self.directory = directory
        self.csv_file_path = csv_file_path
        self.event_dict = {}
        self.lock = threading.Lock()
        self.timer = None

    def on_modified(self, event):
        if not event.is_directory:
            self.queue_event(event.src_path)

    def on_created(self, event):
        if not event.is_directory:
            self.queue_event(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            self.queue_event(event.src_path)

    def queue_event(self, file_path):
        with self.lock:
            self.event_dict[file_path] = time.time()
            if self.timer is None:
                self.timer = threading.Timer(2.0, self.process_event)
                self.timer.start()

    def process_event(self):
        with self.lock:
            self.event_dict = {}
            self.timer = None
        metadata_list = scan_directory(self.directory)
        write_metadata_to_csv(metadata_list, self.csv_file_path)
        print(f"Les métadonnées ont été mises à jour dans {self.csv_file_path}")

if __name__ == "__main__":
    directory = r'C:\Users\tonyt\OneDrive\Bureau\trucs\observation'
    metadata_list = scan_directory(directory)
    csv_file_path = r'C:\Users\tonyt\OneDrive - EPHEC asbl\2324\devII\aout_app\metadata.csv'
    write_metadata_to_csv(metadata_list, csv_file_path)
    print(f"Les métadonnées ont été écrites dans {csv_file_path}")

    event_handler = MetadataEventHandler(directory, csv_file_path)
    observer = Observer()
    observer.schedule(event_handler, path=directory, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()