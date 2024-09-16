import os
import random
import shutil

# Liste des différents fichiers qu'on veut explorer vers les dossiers A CHANGER
dossiers = ['transcription/transcription_1846']

# On crée une liste dans laquelle il aura tous les noms des images
images = []

# on parcourt chaque dossier et sous-dossier et chaque fichier en .tif sont ajouter à images
for dossier in dossiers:
    for dossier_racine, sous_dossiers, fichiers in os.walk(dossier):
        for fichier in fichiers:
            if fichier.endswith(('.xml')): #if fichier.endswith(('.jpg', '.png', '.jpeg', '.tif')):
                chemin_complet = os.path.join(dossier_racine, fichier)
                images.append(chemin_complet)


'''# mélange toutes les images
random.shuffle(images)'''

# set de 25
ensembles_images = [images[i:i + 25] for i in range(0, len(images), 25)]

# path où les dossiers seront créés A CHANGER
dossier_sortie = 'transcription'

# parcours chaque ensemble et on crée un dossier pour chacun
for i, ensemble in enumerate(ensembles_images):
    dossier_ensemble = os.path.join(dossier_sortie, f"Set_{i + 1}")
    os.makedirs(dossier_ensemble, exist_ok=True)  # créer un dossier même s'il existe déjà

    # Copy the images into the folder
    for image in ensemble:
        nom_fichier = os.path.basename(image)
        shutil.copy(image, os.path.join(dossier_ensemble, nom_fichier))