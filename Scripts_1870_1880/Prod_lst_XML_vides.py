import os
import xml.etree.ElementTree as ET

# Chemin du dossier contenant les fichiers XML
xml_folder_path = r'Test_1870/Valais1870'

# Fichier texte où la liste des fichiers vides sera enregistrée
output_txt_path = r'Test_1870/fichiers_xml_vides_1870.txt'

# Liste pour stocker les fichiers XML vides
fichiers_xml_vides = []

# Fonction pour vérifier si un fichier XML est vide
def is_xml_file_empty(xml_file_path):
    try:
        # Charger et parser le fichier XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # Vérifier s'il y a des éléments <String> dans le fichier (ou tout autre élément pertinent)
        namespace = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}
        string_elements = root.findall('.//alto:String', namespace)

        # Si aucun élément pertinent n'est trouvé, le fichier est considéré comme vide
        if not string_elements:
            return True
        return False

    except ET.ParseError:
        # Si le fichier ne peut pas être analysé, on le considère comme vide
        return True

# Parcourir tous les fichiers XML dans le dossier
for xml_file_name in os.listdir(xml_folder_path):
    if xml_file_name.endswith('.xml'):
        xml_file_path = os.path.join(xml_folder_path, xml_file_name)
        print("ok")
        # Vérifier si le fichier XML est vide
        if is_xml_file_empty(xml_file_path):
            fichiers_xml_vides.append(xml_file_name)

# Enregistrer la liste des fichiers vides dans un fichier texte
with open(output_txt_path, 'w', encoding='utf-8') as output_file:
    for xml_file_name in fichiers_xml_vides:
        output_file.write(f"{xml_file_name}\n")

print(f"Liste des fichiers XML vides enregistrée dans {output_txt_path}")
