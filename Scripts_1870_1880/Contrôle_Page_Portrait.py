import xml.etree.ElementTree as ET
import os
import shutil

#Ce scpript a pour objectif de passer sur tout le corpus afin d'identifier les fichiers en portrait
#Cela nous permettra d'évaluer leur nombre et leur nature pour décider comment les traiter
#Corpus 1870 représente pour l'instant 17'510 images. Mais il manque quelques communes.
#Ce script crée 2 fichers txt avec les noms des fichiers vides("Test_1870/Fichiers_XML_vide.txt") et les noms des fichiers en portait ("Test_1870/Portrait_XML_list.txt")
#Ce script crée un dossier ("Test_1870/Folder_portrait") dans lequel se trouve les fichiers xml en format portrait

txt_output_folder = r'Test_1870'
transcription_folder = r'Test_1870/Valais1870'
txt_Portrait_file_path = "Test_1870/Portrait_XML_list.txt"
empty_file_path = "Test_1870/Fichiers_XML_vide.txt"
portrait_files_folder = "Test_1870/Folder_portrait"

if not os.path.exists(portrait_files_folder):
    os.makedirs(portrait_files_folder)

#fonction qui trouve les fichiers vides et les fichiers portraits 
def find_portrait_files(xml_file_name, xml_file_path):
    try:
        # Lire et analyser le fichier XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        namespace = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}
        
        # Extraire les dimensions de la page à partir des attributs WIDTH et HEIGHT de la balise <Page>
        page_element = root.find('.//alto:Page', namespace)
        if page_element is None:  # Cas où il n'y a pas de balise <Page>
            raise ET.ParseError
    
        image_width = int(page_element.get('WIDTH', 0))
        image_height = int(page_element.get('HEIGHT', 0))
        
        if image_width < image_height:
            with open(txt_Portrait_file_path, 'a', encoding='utf-8') as f:
                    f.write(f"{xml_file_name}\n")

    except (ET.ParseError, FileNotFoundError):  # Si le fichier est vide ou non valide
        with open(empty_file_path, 'a', encoding='utf-8') as f:
            f.write(f"{xml_file_name}\n")

#fonction qui compte les fichiers vides et les fichiers portraits 
def count_lines_in_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            return len(lines)
    except FileNotFoundError:
        print(f"Le fichier {file_path} n'existe pas.")
        return 0
    
#fonction qui copie-colle les fichiers portraits dans Folder_portrait
def copy_xml_files_from_txt(txt_file_path, source_folder, destination_folder):
    # Lire les noms des fichiers XML à partir du fichier .txt
    with open(txt_file_path, 'r', encoding='utf-8') as txt_file:
        file_names = txt_file.readlines()

    # Boucler sur chaque fichier listé dans le fichier texte
    for file_name in file_names:
        file_name = file_name.strip()  # Enlever les espaces ou les sauts de ligne
        source_file_path = os.path.join(source_folder, file_name)
        destination_file_path = os.path.join(destination_folder, file_name)

        # Vérifier si le fichier existe dans le dossier source
        if os.path.exists(source_file_path):
            # Copier le fichier vers le dossier de destination
            shutil.copy(source_file_path, destination_file_path)
        else:
            print(f"Fichier non trouvé: {file_name}")

# Utilisation des fonctions
for file in os.listdir(transcription_folder):
    xml_path = os.path.join(transcription_folder, file)
    find_portrait_files(file,xml_path)
    
nombre_de_Portrait = count_lines_in_file(txt_Portrait_file_path)
nombre_de_fichiers_vides = count_lines_in_file(empty_file_path)
print(f"Nombre de fichiers en portrait: {nombre_de_Portrait}")
print(f"Nombre de fichiers vides: {nombre_de_fichiers_vides}")

copy_xml_files_from_txt(txt_Portrait_file_path,transcription_folder,portrait_files_folder)