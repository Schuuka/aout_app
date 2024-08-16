import unittest
import os
import csv
import tempfile
from datetime import datetime
from aout_app import get_metadata, scan_dir, write_csv, Monitor, Shell

class TestAoutApp(unittest.TestCase):

    def setUp(self):
        # Créer un répertoire temporaire pour les tests
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_file_path = os.path.join(self.temp_dir.name, 'test_file.txt')
        with open(self.temp_file_path, 'w') as temp_file:
            temp_file.write('test content')

    def tearDown(self):
        # Nettoyer le répertoire temporaire après les tests
        self.temp_dir.cleanup()

    def test_get_metadata(self):
        # Tester la récupération des données d'un fichier
        metadata = get_metadata(self.temp_file_path)
        self.assertEqual(metadata['name'], 'test_file.txt')
        self.assertIn('creation_time', metadata)
        self.assertIn('modification_time', metadata)
        self.assertEqual(metadata['size'], 12)

    def test_scan_dir(self):
        # Tester le scan d'un répertoire pour récupérer les métadonnées des fichiers
        metadata_list = scan_dir(self.temp_dir.name)
        self.assertEqual(len(metadata_list), 1)
        self.assertEqual(metadata_list[0]['name'], 'test_file.txt')

    def test_write_csv(self):
        # Tester l'écriture des données dans un fichier CSV
        metadata_list = scan_dir(self.temp_dir.name)
        csv_file_path = os.path.join(self.temp_dir.name, 'metadata.csv')
        write_csv(metadata_list, csv_file_path)
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['name'], 'test_file.txt')

    def test_monitor(self):
        # Tester la surveillance d'un répertoire pour les nouveaux fichiers
        csv_file_path = os.path.join(self.temp_dir.name, 'metadata.csv')
        monitor = Monitor(self.temp_dir.name, csv_file_path)
        event = type('Event', (object,), {'is_directory': False, 'src_path': self.temp_file_path})
        monitor.on_created(event)
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['name'], 'test_file.txt')

    def test_shell(self):
        # Tester la création et la suppression de fichiers via le shell
        shell = Shell(self.temp_dir.name, '')
        new_file_name = 'new_test_file.txt'
        shell.do_create(new_file_name)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir.name, new_file_name)))
        shell.do_delete(new_file_name)
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir.name, new_file_name)))

if __name__ == '__main__':
    unittest.main()