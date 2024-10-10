import os
import random
import shutil

#Ce script crée un dossier "Set_2" dans le dossier "Transcriptions" avec 50 XML issus du corpus pour faire des tests aléatoire  

# Chemin du dossier contenant les fichiers XML
xml_folder =  r'Scripts_1870_1880/Transcriptions/Set_1'
destination_folder = r'Scripts_1870_1880/Test_1880'

# Créer le nouveau dossier "Set_2" s'il n'existe pas
nouveau_dossier = os.path.join(destination_folder, 'Set_1')
if not os.path.exists(nouveau_dossier):
    os.makedirs(nouveau_dossier)

# Nombre de fichiers à sélectionner
nombre_fichiers_a_selectionner = 20

# Récupérer tous les fichiers XML dans le dossier
fichiers_xml = [f for f in os.listdir(xml_folder) if f.endswith('.xml')]

# Sélectionner 50 fichiers au hasard
fichiers_selectionnes = random.sample(fichiers_xml, nombre_fichiers_a_selectionner)

# Copier chaque fichier sélectionné dans le nouveau dossier "set2"
for fichier in fichiers_selectionnes:
    source = os.path.join(xml_folder, fichier)
    destination = os.path.join(nouveau_dossier, fichier)
    shutil.copy(source, destination)

