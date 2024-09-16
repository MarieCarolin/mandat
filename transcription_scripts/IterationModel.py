#ce script permet de l'itération des modèles sur le corpus d'image et le classement des fichiers XML dans un dossier "transcription"
import subprocess
import os
import shutil

def main():
    #Première partie : on itère les modèles pour créer des XML
    i = 92
    while i < 93: #(1 set de 25 = ~40minutes)
        subprocess.run(f'kraken -a -I "Sets/Set_{i}/*.jpg" -o .xml segment -bl -i models/blla.mlmodel ocr -m models/KrakenTranscription.mlmodel',shell=True) #permet d'appliquer les modèles en ligne de commande

    #Deuxième partie : on classe les fichiers XML
        dossier_path = f'Sets/Set_{i}' #chemin vers le dossier où se trouve les fichiers JPG et XML
        fichiers = [file for file in os.listdir(dossier_path) if file.endswith(".xml")] #permet de sélectionner uniquement les fichiers XML qui se trouvent dans dossier_path

        a = 0
        while a < len(fichiers): #on itère sur tous les fichiers XML qui se trouve à dossier_path
            fichier_name = fichiers[a]
            source_path = os.path.join(dossier_path, fichier_name) #Path "source" du fichier XML
            destination_path = f"/home/marie-caroline/Bureau/Test_Kranken/scripts/transcription/{fichier_name}" #Path "définitif" pour le fichier XML
            shutil.move(source_path, destination_path) #Modification du Path pour le fichier XML : on remplace source_path par destination_path
            a += 1

        i += 1

main()




