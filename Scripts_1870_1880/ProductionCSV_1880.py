import os
import re
import xml.etree.ElementTree as ET
import numpy as np
from sklearn.cluster import KMeans
import csv
#Ce code a pour objectif de gérer les données des fichiers XML obtenu par OCR pour 1870
#Ce code organise les données des prénoms et des noms dans un dictionnaire, recrée les noms composés et recrée le lien entre prénom et nom de famille
#Ce code gère les images en format protrait qui ont moins données et qui ne peuvent pas être gérées de la même manière que les autres 
#Ce code peut  génèrer  des fichiers txt dans lesquels sont organisés les données. (generate_txt_output)
#Contrairement au scripts de 1829, 1837, 1846 et 1850, ce code ne nécéssite pas d'utiliser les numérisations, il prend les infos directement dans les fichiers xml
#l'output final de ce code est un fichier csv

# Chemins vers les dossiers contenant les fichiers XML et JPG.
transcription_folder = r'Scripts_1870_1880/Test_1880'

# lsts
output_list = []  # output final
Pages_sans_text = [
    
]  # lst de pages sans texte

# Liste pour stocker les fichiers XML avec des erreurs
fichiers_avec_erreurs = []

# Liste des fichiers qui ont échoué avec 6 clusters mais fonctionnent avec 4
fichiers_6_to_4 = []

# Dictionnaires pour stocker les résultats selon le nombre de clusters
final_dict_6_clusters = {}  # Fichiers traités avec 6 clusters
final_dict_4_clusters = {}  # Fichiers traités avec 4 clusters après échec avec 6

# Liste des mots à exclure (affiliation) ajouter des exclusions en allemand pour la précision
exclusion_terms = [
    "fils", "père", "mère", "fille", "grand-père", "grand-mère", "femme", "fem","épouse","époux", "mari" # Français
    "Sohn", "Tochter", "Tochten", "Tochm" "Vater", "Mutter", "Grossvater", "Grossmutter", "Frau"  # Allemand (standard)
    "grandpere", "grandmere", "Grandpere", "Grandmere", "Grand-Pere", "Grand-Mere", "Grandpère", "Grandmère",  # Variantes sans accent
    "soeur", "frère", "seour", "bel", "belle", "petite", "petit", "Père", "Mère", "Fils", "Fille", "Femme", "Fem", "Epouse", "Epoux", "Mari", # Variantes françaises
    "Soeur", "Frère", "Beau-Père", "Beau-Mère", "Belle-Mère", "Beau-Frère", "Belle-Soeur",  # Français avec majuscules
    "Bruder", "Schwester", "Schwager", "Schwägerin", "Schwiegervater", "Schwiegermutter",  # Allemand (frère, soeur, beaux-parents)
    "domestique", "Domestique", "Etudiant", "étudiant", "Etudiante", "étudiante","instituteur", "Instituteur", "institutrice", "Institutrice"
]
# Fonction pour contrôler si c'est un portrait ou non 

# Fonction pour appliquer le clustering et organiser les données dans un dictionnaire
def apply_clustering_and_create_dict(xml_file_name, xml_file_path, num_clusters, filter_hpos=None):
    try:
        # Lire et analyser le fichier XML
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # Extraire les éléments XML avec la balise <alto:String>
        namespace = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}
        string_elements = root.findall('.//alto:String', namespace)
        page_element = root.find('.//alto:Page', namespace)

        # Extraire les valeurs HPOS et VPOS, les convertir en entiers
        hpos_values = np.array([int(string_element.get('HPOS', 0)) for string_element in string_elements])
        vpos_values = np.array([int(string_element.get('VPOS', 0)) for string_element in string_elements])
        image_width = int(page_element.get('WIDTH', 0))
        image_height = int(page_element.get('HEIGHT', 0))
        moitie_image = image_width / 2  # Moitié verticale de la page

        #géreer les images en portraits
        if image_width < image_height:
            return process_portrait_files(xml_file_name, xml_file_path,4)

        else : 
            # Appliquer le filtre pour ne prendre en compte que les données avant la moitié de l'image (si demandé)
            if filter_hpos:
                indices = np.where(hpos_values < moitie_image)[0]
                hpos_values = hpos_values[indices]
                vpos_values = vpos_values[indices]
                string_elements = [string_elements[i] for i in indices]

            # Reshape pour clustering
            hpos_values = hpos_values.reshape(-1, 1)
            vpos_values = vpos_values.reshape(-1, 1)

            # Appliquer KMeans pour séparer les valeurs HPOS et VPOS en `num_clusters` clusters
            kmeans_hpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_hpos = kmeans_hpos.fit_predict(hpos_values)

            kmeans_vpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_vpos = kmeans_vpos.fit_predict(vpos_values)

            # Calcul de la médiane des valeurs HPOS pour chaque Cluster
            median_values = []
            for i in range(num_clusters):
                cluster_points_hpos = hpos_values[clusters_hpos == i]
                cluster_points_vpos = vpos_values[clusters_vpos == i]
                median_hpos_value = int(np.median(cluster_points_hpos))
                median_vpos_value = int(np.median(cluster_points_vpos))
                median_values.append((i, median_hpos_value, median_vpos_value))

            # Trier les clusters par leur position HPOS
            sorted_clusters = sorted(median_values, key=lambda x: x[1])

            # Organiser le contenu en clusters
            cluster_content = {i: [] for i in range(num_clusters)}
            for i, string_element in enumerate(string_elements):
                content = string_element.get('CONTENT')
                hpos = int(string_element.get('HPOS', 0))
                vpos = int(string_element.get('VPOS', 0))
                assigned_cluster_hpos = clusters_hpos[i]
                cluster_content[assigned_cluster_hpos].append((hpos, vpos, content))

            # Trier les éléments dans chaque cluster par HPOS puis VPOS
            for i in range(num_clusters):
                cluster_content[i] = sorted(cluster_content[i], key=lambda x: (x[0], x[1]))

            # Création du dictionnaire pour stocker les données XML par catégories
            current_xml_dict = {xml_file_name: {'Last Name': [], 'First Name': [], 'Other': []}}
            cluster_names = {1: 'Last Name', 2: 'First Name', 3: 'Other'}  # Organisation du dictionnaire

            # Ajoute chaque élément du cluster dans le dictionnaire
            for i, cluster_data in enumerate(sorted_clusters, start=1):
                cluster_index, _, _ = cluster_data
                cluster_content_data = [(hpos, vpos, content) for hpos, vpos, content in cluster_content[cluster_index]]
                cluster_content_data.sort(key=lambda x: x[1])  # Tri par VPOS
                
                # Nettoyage des données, puis rangement des données dans le dictionnaire
                for hpos, vpos, content in cluster_content_data:
                    if hpos > moitie_image or content in [" ", "/", "-"] or re.match(r'.*\d+.*', content) or re.match(r'[A-Z]{3,}', content) or content in exclusion_terms:
                        pass  # Filtrage du contenu non pertinent

                    else:
                        if i != 4:
                            current_xml_dict[xml_file_name][cluster_names[i]].append((content, vpos, hpos))
                        else:
                            current_xml_dict[xml_file_name][cluster_names[3]].append((content, vpos, hpos))

            return current_xml_dict

    except Exception as e:
        raise e  # Relancer l'exception pour la capturer à un autre niveau


# Fonction pour gérer les prénoms composés, avec filtrage des termes d'affiliation avant le calcul de la médiane
def handle_composed_first_names(current_xml_dict, xml_file_name):
    FirstName_str = current_xml_dict.get(xml_file_name).get("First Name")
    if not FirstName_str or len(FirstName_str) == 0:
        return  # Aucun prénom à traiter, on quitte la fonction
    
    len_FirstName_str = len(FirstName_str)
    FirstName_Hpos = []
    for i in range(len_FirstName_str):
        FirstName_Hpos.append((FirstName_str[i][2]))
    
    FirstName_Hpos_array = np.array(FirstName_Hpos)
    FirstName_Hpos_median = np.median(FirstName_Hpos_array)

    # Calcul de l'écart médian absolu. Cela permet d'obtenir une valeur de référence pour identifier la deuxième partie du nom composé
    Ecart_Median = []
    for FirstName in FirstName_str:
        Valeur_absolue_Ecart = abs(FirstName_Hpos_median - FirstName[2])
        Ecart_Median.append(Valeur_absolue_Ecart)

    len_Ecart_Median = len(Ecart_Median)
    Ecart_Median_Array = np.array(Ecart_Median)
    Ecart_Median_Absolu = np.sum(Ecart_Median_Array)/len_Ecart_Median
    Ecart_Median_Absolu_PLUS_Median = Ecart_Median_Absolu + FirstName_Hpos_median
    
    # Tri des contenus de la colonne Prénom : Première partie pour les prénoms proches de la médiane, deuxième partie pour les prénoms proches de la médiane + de l'écart absolu
    Premiere_Partie = []
    Deuxieme_Partie =[]
    for FirstName in FirstName_str: 
        Ecart_Hpos_Mediane = abs(FirstName_Hpos_median - FirstName[2])
        Ecart_Hpos_Median_Absolu_PLUS_Median = abs(Ecart_Median_Absolu_PLUS_Median - FirstName[2])
        if Ecart_Hpos_Mediane < Ecart_Hpos_Median_Absolu_PLUS_Median: # Première partie du prénom
            Premiere_Partie.append(FirstName)
    
        else :  # Deuxième partie du prénom
            Deuxieme_Partie.append(FirstName)
              
    # Vérifier s'il y a des prénoms dans chaque partie
    if not Premiere_Partie or not Deuxieme_Partie:
        return  # Si une des parties est vide, on ne fait rien

    # Correspondre chaque prénom de la Deuxième Partie à un prénom de la Première Partie en fonction de VPOS
    for second_part in Deuxieme_Partie:
        closest_first_part = None
        min_vpos_diff = float('inf')

        # Trouver la première partie avec la différence VPOS la plus petite
        for first_part in Premiere_Partie:
            vpos_diff = abs(second_part[1] - first_part[1])
            if vpos_diff < min_vpos_diff:
                min_vpos_diff = vpos_diff
                closest_first_part = first_part

        # Combiner les deux parties du prénom (première et deuxième)
        if closest_first_part:
            index_in_premiere_partie = Premiere_Partie.index(closest_first_part)
            combined_name = f"{closest_first_part[0]} {second_part[0]}"
            Premiere_Partie[index_in_premiere_partie] = (combined_name, closest_first_part[1], closest_first_part[2])

    # Trier la première partie par VPOS
    Premiere_partie_triee = sorted(Premiere_Partie, key=lambda x: x[1])

    # Mettre à jour le dictionnaire avec les prénoms composés reconstruits
    current_xml_dict[xml_file_name]["First Name"] = Premiere_partie_triee

# Fonction pour lier les prénoms aux noms de famille, en filtrant les termes d'affiliation
def link_first_name_last_name(current_xml_dict, xml_file_name, output_list):
    print('linked first name ')
    FirstName_str = current_xml_dict.get(xml_file_name).get("First Name")
    LastName_str = current_xml_dict.get(xml_file_name).get("Last Name")
    
    if len(FirstName_str) == 0 and len(LastName_str) == 0:
        return  # Si aucune donnée n'est présente, on ne fait rien

    # Création d'une liste qui contiendra : le nom du fichier xml, le nom de famille, le prénom, la valeur vpos(y), la valeur hpos(x)
    FirstName_LastName = []
    for name in FirstName_str:
        # Filtrer les prénoms contenant des termes d'affiliation
        if any(term.lower() in name[0].lower() for term in exclusion_terms):
            continue
        # Ajouter chaque prénom avec des informations initiales, le nom de famille est "?" par défaut
        FirstName_LastName.append([xml_file_name, "?", name[0], name[1], name[2]])  # [xml file, nom de famille, prénom, vpos, hpos]
    
    # Tri de la liste FirstName_LastName selon la position VPOS pour faciliter la correspondance avec les noms de famille
    FirstName_LastName_sorted = sorted(FirstName_LastName, key=lambda x: x[3])  # Trie par vpos (y)

    # Comparaison des valeurs VPOS de chaque prénom et nom de famille pour recréer le lien
    for lastname in LastName_str:
        # Initialisation de la première différence pour comparer les valeurs VPOS
        abs_difference = abs(FirstName_LastName_sorted[0][3] - lastname[1])
        difference = [abs_difference, FirstName_LastName_sorted[0][2], lastname[0], 0, FirstName_LastName_sorted[0][3]]

        for i, name in enumerate(FirstName_LastName_sorted):
            abs_lastname_name = abs(lastname[1] - name[3])
            if abs_lastname_name <= difference[0]:
                difference = [abs_lastname_name, name[2], lastname[0], i, name[3]]

        # Mettre à jour le nom de famille dans FirstName_LastName pour le prénom correspondant
        FirstName_LastName[difference[3]][1] = lastname[0]

    # Ajouter la liste organisée dans l'output final avec les noms et prénoms associés
    output_list.append(FirstName_LastName)  # [xml file, nom de famille, prénom, vpos, hpos]
    # Génération des fichiers .txt avec les résultats
    # generate_txt_output(xml_file_name, FirstName_LastName)
    # Génération d'un ficiher csv
    generate_csv_output(output_list)

# Fonction pour générer des fichiers .txt
'''def generate_txt_output(xml_file_name, FirstName_LastName):
    txt_file_path = os.path.join(txt_output_folder, f"{xml_file_name.replace('.xml', '')}.txt")
    with open(txt_file_path, 'w', encoding='utf-8') as f:
        for entry in FirstName_LastName:
            f.write(f"XML File: {entry[0]}\nNom de famille: {entry[1]}\nPrénom: {entry[2]}\nVPOS (y): {entry[3]}\nHPOS (x): {entry[4]}\n\n")'''

# Fonction pour générer le csv à partir de "output_list"
def generate_csv_output(output):
    output_forCSV =[]
    for xml in output:
        for line in xml:
            output_forCSV.append(line)

    output_forCSV.sort(key=lambda x: (x[0], x[3]))
    header = ['File', 'Last Name', 'First', 'YPos', 'XPos']

    with open("Output1880.csv", "w", newline='',encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(header)
        csv_writer.writerows(output_forCSV)

# Fonction pour traiter les fichiers en portrait et extraire le contenu avant la moitié verticale
def process_portrait_files(xml_file_name, xml_file_path,num_clusters):
        print(xml_file_name)
        try:
            # Lire et analyser le fichier XML
            tree = ET.parse(xml_file_path)
            root = tree.getroot()
            namespace = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}

            # Extraire les dimensions de la page à partir des attributs WIDTH et HEIGHT de la balise <Page>
            page_element = root.find('.//alto:Page', namespace)
            image_width = int(page_element.get('WIDTH', 0))
            image_height = int(page_element.get('HEIGHT', 0))
            moitie_image = image_width / 2  # Moitié verticale de la page

            # Extraire les éléments XML avec la balise <alto:String>
            string_elements = root.findall('.//alto:String', namespace)

            # Extraire les valeurs HPOS et VPOS, les convertir en entiers
            hpos_values = np.array([int(string_element.get('HPOS', 0)) for string_element in string_elements])
            vpos_values = np.array([int(string_element.get('VPOS', 0)) for string_element in string_elements])

            #Conserver que les données avant la moitié de l'image
            indices = np.where(hpos_values < moitie_image)[0]
            hpos_values = hpos_values[indices]
            string_elements = [string_elements[i] for i in indices]
            
            # Reshape pour clustering
            hpos_values = hpos_values.reshape(-1, 1)
            vpos_values = vpos_values.reshape(-1, 1)

            # Appliquer KMeans pour séparer les valeurs HPOS et VPOS en `num_clusters` clusters
            kmeans_hpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_hpos = kmeans_hpos.fit_predict(hpos_values)

            kmeans_vpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_vpos = kmeans_vpos.fit_predict(vpos_values)

            # Calcul de la médiane des valeurs HPOS pour chaque Cluster
            median_values = []
            for i in range(num_clusters):
                cluster_points_hpos = hpos_values[clusters_hpos == i]
                cluster_points_vpos = vpos_values[clusters_vpos == i]
                median_hpos_value = int(np.median(cluster_points_hpos))
                median_vpos_value = int(np.median(cluster_points_vpos))
                median_values.append((i, median_hpos_value, median_vpos_value))

            # Trier les clusters par leur position HPOS
            sorted_clusters = sorted(median_values, key=lambda x: x[1])

            # Organiser le contenu en clusters
            cluster_content = {i: [] for i in range(num_clusters)}
            for i, string_element in enumerate(string_elements):
                content = string_element.get('CONTENT')
                hpos = int(string_element.get('HPOS', 0))
                vpos = int(string_element.get('VPOS', 0))
                assigned_cluster_hpos = clusters_hpos[i]
                cluster_content[assigned_cluster_hpos].append((hpos, vpos, content))

            # Trier les éléments dans chaque cluster par HPOS puis VPOS
            for i in range(num_clusters):
                cluster_content[i] = sorted(cluster_content[i], key=lambda x: (x[0], x[1]))

            # Création du dictionnaire pour stocker les données XML par catégories
            current_xml_dict = {xml_file_name: {'Last Name': [], 'First Name': [], 'Other': []}}
            cluster_names = {1: 'Last Name', 2: 'First Name', 3: 'Other'}  # Organisation du dictionnaire

            # Ajoute chaque élément du cluster dans le dictionnaire
            for i, cluster_data in enumerate(sorted_clusters, start=1):
                cluster_index, _, _ = cluster_data
                cluster_content_data = [(hpos, vpos, content) for hpos, vpos, content in cluster_content[cluster_index]]
                cluster_content_data.sort(key=lambda x: x[1])  # Tri par VPOS
                
                # Nettoyage des données, puis rangement des données dans le dictionnaire
                for hpos, vpos, content in cluster_content_data:
                    if hpos > moitie_image or content in [" ", "/", "-"] or re.match(r'.*\d+.*', content) or re.match(r'[A-Z]{3,}', content) or content in exclusion_terms:
                        pass  # Filtrage du contenu non pertinent

                    else:
                        if i != 4:
                            current_xml_dict[xml_file_name][cluster_names[i]].append((content, vpos, hpos))
                        else:
                            current_xml_dict[xml_file_name][cluster_names[3]].append((content, vpos, hpos))

            return current_xml_dict

        except Exception as e:
            print(f"Erreur lors du traitement du fichier en portrait {xml_file_name}: {e}")

# Partie principale : appel de la fonction pour chaque fichier XML
for subfolder_name in os.listdir(transcription_folder):
    xml_folder = os.path.join(transcription_folder, subfolder_name)

    for xml_file_name in os.listdir(xml_folder):
        if xml_file_name.endswith('.xml') and xml_file_name not in Pages_sans_text:
            try:
                xml_file_path = os.path.join(xml_folder, xml_file_name)

                current_dict = apply_clustering_and_create_dict(xml_file_name, xml_file_path, num_clusters=6)
                final_dict_6_clusters.update(current_dict)

                # Ajout de la gestion des prénoms composés
                handle_composed_first_names(current_dict, xml_file_name)

                # Restitution du lien entre prénom et nom de famille
                link_first_name_last_name(current_dict, xml_file_name, output_list)

            except Exception as e:
                try:
                    current_dict = apply_clustering_and_create_dict(xml_file_name, xml_file_path, num_clusters=4, filter_hpos=True)
                    final_dict_4_clusters.update(current_dict)
                    fichiers_6_to_4.append(xml_file_name)

                    # Ajout de la gestion des prénoms composés
                    handle_composed_first_names(current_dict, xml_file_name)

                    # Restitution du lien entre prénom et nom de famille après traitement avec 4 clusters
                    link_first_name_last_name(current_dict, xml_file_name, output_list)

                except Exception as e:
                    fichiers_avec_erreurs.append(xml_file_name)
