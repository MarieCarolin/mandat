#ce script permet de l'itération des modèles sur le corpus d'image automatiquement
import subprocess
import os
import shutil
def main():
    i = 1
    while i < 9: #on itère le modèle 8 fois par set de 25, envrion 5h20 (1 set de 25 = ~40minutes)
        subprocess.run(f'kraken -a -I "Sets/Set_{i}/*.jpg" -o .xml segment -bl -i models/blla.mlmodel ocr -m models/KrakenTranscription.mlmodel',shell=True)
        os.mkdir(f"/home/marie-caroline/Bureau/Test_Kranken/scripts/transcription/Set_{i}")

        dossier_path = f"Sets/Set_{i}/"
        fichiers = [file for file in os.listdir(dossier_path) if file.endswith(".xml")]

        a = 0
        while a < len(fichiers):
            fichier_name = fichiers[a]
            source_path = os.path.join(dossier_path, fichier_name)
            destination_path = f"/home/marie-caroline/Bureau/Test_Kranken/scripts/transcription/Set_{i}/{fichier_name}"
            shutil.move(source_path, destination_path)
            a += 1

        i += 1

main()




