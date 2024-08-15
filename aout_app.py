import os
import csv
from datetime import datetime

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

if __name__ == "__main__":
    directory = r'C:\Users\tonyt\OneDrive\Bureau\trucs\observation'
    metadata_list = scan_directory(directory)
    csv_file_path = r'C:\Users\tonyt\OneDrive - EPHEC asbl\2324\devII\aout_app\metadata.csv'
    write_metadata_to_csv(metadata_list, csv_file_path)
    print(f"Les métadonnées ont été écrites dans {csv_file_path}")