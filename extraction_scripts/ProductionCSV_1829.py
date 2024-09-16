# Ce code permet de restituer les contenus des pages des recensements valaisans de 1846 en fichier CSV.
# Il y a 4 parties dans ce code :
# 1. Utilisation du clustering pour séparer le contenu en deux colonnes : Prénom, Nom de Famille
# 2. Restitution des prénoms composés dans la colonne Prénom
# 3. Restitution du lien entre Prénom et Nom de Famille
# 4. Transformation des données en fichier CSV

import os
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import KMeans
import csv

# Chemin vers les dossiers où se trouvent les fichiers XML et JPG
transcription_folder = 'transcription'
sets_folder = 'Sets'

# lsts
output_list = [] #output final
Pages_sans_text = ['AEV_3090_1829_Entremont_Index.xml', 'AEV_3090_1829_Goms_Index.xml'] #lst de pages sans texte 
output_list_gauche = []
output_list_droite = []

# Partie 1 - Utilisation du clustering pour séparer le contenu en deux colonnes : Prénom, Nom de Famille
# Itère sur les sous-dossiers dans le dossier "transcription"
for subfolder_name in os.listdir(transcription_folder):
    # Construction des chemins vers les dossiers actuels de la boucle
    xml_folder = os.path.join(transcription_folder, subfolder_name)
    img_folder = os.path.join(sets_folder, subfolder_name)

    # Itère sur tous les fichiers XML dans le sous-dossiers actuel de la boucle 
    for xml_file_name in os.listdir(xml_folder):
        print(xml_file_name)
        if xml_file_name.endswith('.xml') and xml_file_name not in Pages_sans_text :
            # Construction du chemin pour le fichier XML actuel dans la boucle, ainsi que le fichier JPG.
            xml_file_path = os.path.join(xml_folder, xml_file_name)
            img_file_path = os.path.join(img_folder, xml_file_name.replace('.xml', '.jpg'))

            # Calculer la valeur de la moitié de l'image
            img = Image.open(img_file_path)
            image_width = img.width
            moitie_image = image_width / 2

            # Permet de lire et analyser des fichiers XML
            # Permet de détecter l'élément racine, puis de naviguer dans l'arborescence XML
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Création d'une liste de tous les éléments XML avec la balise <alto:String>
            namespace = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}
            string_elements = root.findall('.//alto:String', namespace)

            elements_on_page = []
            elements_on_page_gauche = []
            elements_on_page_droite = []

            for element in string_elements:
                hpos = element.get('HPOS')
                vpos = element.get('VPOS')
                content = element.get('CONTENT')

                if vpos is None: # Contrôle la valeur de HPOS : si elle est None (nulle), c'est une erreur d'OCR ; on lui attribue une valeur de 0
                    vpos = int(0)
                if hpos is None: # Contrôle la valeur de HPOS : si elle est None (nulle), c'est une erreur d'OCR ; on lui attribue une valeur de 0
                    hpos = int(0)

                elements_on_page.append([content,hpos,vpos])
                if int(hpos) < moitie_image:
                    elements_on_page_gauche.append([content,hpos,vpos])
                else :
                    elements_on_page_droite.append([content,hpos,vpos])


            # Défini un nombre de cluster
            num_clusters = 4

            # Corrections pour les pages blanches
            if len(elements_on_page_gauche) < 4 : 
                num_clusters = 1
                if len(elements_on_page_gauche) == 0 :
                    elements_on_page_gauche.append(["-",0,0])

            if len(elements_on_page_droite) < 4 : 
                num_clusters = 1
                if len(elements_on_page_droite) == 0 :
                    elements_on_page_droite.append(["-",0,0])
                
            # Extraire les valeurs HPOS et VPOS, les convertir en entiers, puis les remodeler en un tableau 2D.
            # Pour la page gauche
            hpos_values_gauche = np.array([int(string_element[1]) for string_element in elements_on_page_gauche])
            vpos_values_gauche = np.array([int(string_element[2]) for string_element in elements_on_page_gauche])

            hpos_values_gauche = hpos_values_gauche.reshape(-1, 1)
            vpos_values_gauche = vpos_values_gauche.reshape(-1, 1)

            # Pour la page droite 
            hpos_values_droite = np.array([int(string_element[1]) for string_element in elements_on_page_droite])
            vpos_values_droite = np.array([int(string_element[2]) for string_element in elements_on_page_droite])

            hpos_values_droite = hpos_values_droite.reshape(-1, 1)
            vpos_values_droite = vpos_values_droite.reshape(-1, 1)

            # Appliquer un clustering KMeans basé sur les valeurs HPOS gauche et droite
            kmeans_hpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_hpos_gauche = kmeans_hpos.fit_predict(hpos_values_gauche)
            clusters_hpos_droite = kmeans_hpos.fit_predict(hpos_values_droite)

            # Appliquer un clustering KMeans basé sur les valeurs VPOS gauche et droite
            kmeans_vpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_vpos_gauche = kmeans_vpos.fit_predict(vpos_values_gauche)
            clusters_vpos_droite = kmeans_vpos.fit_predict(vpos_values_droite)

            # Calcul de la mediane des valeurs HPOS pour chaque Cluster à gauche
            median_values_gauche = []
            for i in range(num_clusters):
                cluster_points_hpos_gauche = hpos_values_gauche[clusters_hpos_gauche == i]
                cluster_points_vpos_gauche = vpos_values_gauche[clusters_vpos_gauche == i]
                median_hpos_value_gauche = int(np.median(cluster_points_hpos_gauche))
                median_vpos_value_gauche = int(np.median(cluster_points_vpos_gauche))
                median_values_gauche.append((i, median_hpos_value_gauche, median_vpos_value_gauche))

            # Calcul de la mediane des valeurs HPOS pour chaque Cluster à droite
            median_values_droite = []
            for i in range(num_clusters):
                cluster_points_hpos_droite = hpos_values_droite[clusters_hpos_droite == i]
                cluster_points_vpos_droite = vpos_values_droite[clusters_vpos_droite == i]
                median_hpos_value_droite = int(np.median(cluster_points_hpos_droite))
                median_vpos_value_droite = int(np.median(cluster_points_vpos_droite))
                median_values_droite.append((i, median_hpos_value_droite, median_vpos_value_droite))

            # Organise le contenu des XML en fonction de leur appartenance au cluster
            # Gauche
            sorted_clusters_gauche = sorted(median_values_gauche, key=lambda x: x[1])
            cluster_content_gauche = {i: [] for i in range(num_clusters)}

            # Droite
            sorted_clusters_droite = sorted(median_values_droite, key=lambda x: x[1])
            cluster_content_droite = {i: [] for i in range(num_clusters)}

            # Enregistre les valeurs de HPOS et VPOS dans les variables à gauche
            for i, string_element in enumerate(elements_on_page_gauche):
                content_gauche = string_element[0]
                hpos_str_gauche = string_element[1]
                if hpos_str_gauche is not None: 
                    hpos_gauche = int(hpos_str_gauche)
                else:
                    hpos_gauche = 0

                vpos_str_gauche = string_element[2]
                if vpos_str_gauche is not None: 
                    vpos_gauche = int(vpos_str_gauche)
                else:
                    vpos_gauche = 0

                assigned_cluster_hpos_gauche = clusters_hpos_gauche[i]
                assigned_cluster_vpos_gauche = clusters_vpos_gauche[i]
                cluster_content_gauche[assigned_cluster_hpos_gauche].append((hpos_gauche, vpos_gauche, content_gauche))

            # Enregistre les valeurs de HPOS et VPOS dans les variables à droite
            for i, string_element in enumerate(elements_on_page_droite):
                content_droite = string_element[0]
                hpos_str_droite = string_element[1]
                if hpos_str_droite is not None:
                    hpos_droite = int(hpos_str_droite)
                else:
                    hpos_droite = 0

                vpos_str_droite = string_element[2]
                if vpos_str_droite is not None: 
                    vpos_droite = int(vpos_str_droite)
                else:
                    vpos_droite = 0

                assigned_cluster_hpos_droite = clusters_hpos_droite[i]
                assigned_cluster_vpos_droite = clusters_vpos_droite[i]
                cluster_content_droite[assigned_cluster_hpos_droite].append((hpos_droite, vpos_droite, content_droite))

            # Organisation les éléments dans chaque cluster à gauche et à droite
            for i in range(num_clusters):
                cluster_content_gauche[i] = sorted(cluster_content_gauche[i], key=lambda x: x[0])
                cluster_content_droite[i] = sorted(cluster_content_droite[i], key=lambda x: x[0])

            # Gauche
            # Ajoute chaque élément des Cluster dans cluster_dict gauche 
            current_xml_dict_gauche = {xml_file_name: {'Last Name': [], 'First Name': [], 'Other': []}}
            cluster_names_gauche = {1: 'Last Name', 2: 'First Name', 3: 'Other'} # Dictionnaire est organisé ainsi d'abord par XML file, ensuite par colonne
            for i, cluster_data in enumerate(sorted_clusters_gauche, start=1):
                cluster_index_gauche, _, _ = cluster_data
                cluster_content_data_gauche = [(hpos, vpos, content) for hpos, vpos, content in cluster_content_gauche[cluster_index_gauche]]
                cluster_content_data_gauche.sort(key=lambda x: x[1]) # Organisation les éléments dans chaque cluster en fonction de vpos

                # Nettoyage des données, puis rangement des données dans le dictionnaire
                for hpos, vpos, content in cluster_content_data_gauche:
                    if hpos > moitie_image/2 or content in [" ", "/", "-"] or re.match(r'.*\d+.*', content) or re.match(r'[A-Z]{3,}', content):
                        pass
                    else:
                        if i != 4:
                            current_xml_dict_gauche[xml_file_name][cluster_names_gauche[i]].append((content, vpos, hpos))
                        else:
                            current_xml_dict_gauche[xml_file_name][cluster_names_gauche[3]].append((content, vpos, hpos))
            # Droite
            # Ajoute chaque élément des Cluster dans cluster_dict droite
            current_xml_dict_droite = {xml_file_name: {'Last Name': [], 'First Name': [], 'Other': []}}
            cluster_names_droite = {1: 'Last Name', 2: 'First Name', 3: 'Other'} # Dictionnaire est organisé ainsi d'abord par XML file, ensuite par colonne
            for i, cluster_data in enumerate(sorted_clusters_droite, start=1):
                cluster_index_droite, _, _ = cluster_data
                cluster_content_data_droite = [(hpos, vpos, content) for hpos, vpos, content in cluster_content_droite[cluster_index_droite]]
                cluster_content_data_droite.sort(key=lambda x: x[1]) # Organisation les éléments dans chaque cluster en fonction de vpos

                # Nettoyage des données, puis rangement des données dans le dictionnaire
                for hpos, vpos, content in cluster_content_data_droite:
                    if hpos > moitie_image + moitie_image/2 or content in [" ", "/", "-"] or re.match(r'.*\d+.*', content) or re.match(r'[A-Z]{3,}', content):
                        pass
                    else:
                        if i != 4:
                            current_xml_dict_droite[xml_file_name][cluster_names_droite[i]].append((content, vpos, hpos))
                        else:
                            current_xml_dict_droite[xml_file_name][cluster_names_droite[3]].append((content, vpos, hpos))

# Partie 2 - Restituion des prénoms composés dans First Name
            # Calcul de la médiane des valeurs hpos pour les First Name gauche et droite
            FirstName_str_gauche = current_xml_dict_gauche.get(xml_file_name).get("First Name")
            FirstName_str_droite = current_xml_dict_droite.get(xml_file_name).get("First Name")
            len_FirstName_str_gauche = len(FirstName_str_gauche)
            len_FirstName_str_droite = len(FirstName_str_droite)
            FirstName_Hpos_gauche = []
            FirstName_Hpos_droite = []
            for i in range(len_FirstName_str_gauche):
                FirstName_Hpos_gauche.append((FirstName_str_gauche[i][2]))

            for i in range(len_FirstName_str_droite):
                FirstName_Hpos_droite.append((FirstName_str_droite[i][2]))                
            
            FirstName_Hpos_array_gauche = np.array(FirstName_Hpos_gauche)
            FirstName_Hpos_median_gauche = np.median(FirstName_Hpos_array_gauche)

            FirstName_Hpos_array_droite = np.array(FirstName_Hpos_droite)
            FirstName_Hpos_median_droite = np.median(FirstName_Hpos_array_droite)

            # Calcul de l'écart median absolu. Cela permet d'avoir une valeur référence pour identifier la deuxième partie du nom composé
            # Gauche
            Ecart_Median_gauche = []

            for FirstName in FirstName_str_gauche:
                Valeur_absolue_Ecart_gauche = abs(FirstName_Hpos_median_gauche - FirstName[2])
                Ecart_Median_gauche.append(Valeur_absolue_Ecart_gauche)

            len_Ecart_Median_gauche = len(Ecart_Median_gauche)
            Ecart_Median_Array_gauche = np.array(Ecart_Median_gauche)
            Ecart_Median_Absolu_gauche = np.sum(Ecart_Median_Array_gauche)/len_Ecart_Median_gauche
            Ecart_Median_Absolu_PLUS_Median_gauche = Ecart_Median_Absolu_gauche + FirstName_Hpos_median_gauche
            
            # Droite
            Ecart_Median_droite = []
            for FirstName in FirstName_str_droite:
                Valeur_absolue_Ecart_droite = abs(FirstName_Hpos_median_droite - FirstName[2])
                Ecart_Median_droite.append(Valeur_absolue_Ecart_droite)

            len_Ecart_Median_droite = len(Ecart_Median_droite)
            Ecart_Median_Array_droite = np.array(Ecart_Median_droite)
            Ecart_Median_Absolu_droite = np.sum(Ecart_Median_Array_droite)/len_Ecart_Median_droite
            Ecart_Median_Absolu_PLUS_Median_droite = Ecart_Median_Absolu_droite + FirstName_Hpos_median_droite
            
            # Tri des contenus de First Name : Première partie pour les prénoms proche de la médiane, deuxième partie pour les prénoms proches de la médiane + de l'éart absolu
            # Gauche 
            Premiere_Partie_gauche = []
            Deuxieme_Partie_gauche = []

            for FirstName in FirstName_str_gauche: 
                Ecart_Hpos_Mediane_gauche = abs(FirstName_Hpos_median_gauche - FirstName[2])
                Ecart_Hpos_Median_Absolu_PLUS_Median_gauche = abs(Ecart_Median_Absolu_PLUS_Median_gauche - FirstName[2])
                if Ecart_Hpos_Mediane_gauche < Ecart_Hpos_Median_Absolu_PLUS_Median_gauche: 
                    Premiere_Partie_gauche.append(FirstName)
            
                else :  
                    Deuxieme_Partie_gauche.append(FirstName)


            # Droite
            Premiere_Partie_droite = []
            Deuxieme_Partie_droite = []
            for FirstName in FirstName_str_droite: 
                Ecart_Hpos_Mediane_droite = abs(FirstName_Hpos_median_droite - FirstName[2])
                Ecart_Hpos_Median_Absolu_PLUS_Median_droite = abs(Ecart_Median_Absolu_PLUS_Median_droite - FirstName[2])
                if Ecart_Hpos_Mediane_droite < Ecart_Hpos_Median_Absolu_PLUS_Median_droite: 
                    Premiere_Partie_droite.append(FirstName)
            
                else :  
                    Deuxieme_Partie_droite.append(FirstName)
            
            # Attribution de chaque élément dans la deuxième partie à un prénom de première partie en fonction de vpos. 
            # Le code passe sur chaque élément de première partie et compare les valeurs vpos(y).  
            # Gauche
            if len(Premiere_Partie_gauche) == 0 or len(Deuxieme_Partie_gauche) == 0:
                pass
            else :             
                for a,element in enumerate(Deuxieme_Partie_gauche):
                    abs_Plus_petite_difference_gauche = abs(Deuxieme_Partie_gauche[0][1] - Premiere_Partie_gauche[0][1])
                    Plus_petite_difference_gauche = [abs_Plus_petite_difference_gauche,  Deuxieme_Partie_gauche[0][0], Premiere_Partie_gauche[0][0], 0, Premiere_Partie_gauche[0][1],Premiere_Partie_gauche[0][2]]
                    for i,name in enumerate(Premiere_Partie_gauche):
                        abs_name_element_gauche = abs(element[1] - name[1])
                        if abs_name_element_gauche < Plus_petite_difference_gauche[0]:
                            Plus_petite_difference_gauche = [abs_name_element_gauche, element[0], name[0], i, name[1], name[2]] # = [chiffre, prenom, prenom, chiffre, vpos, hpos]
                    
                    if element[0] in Plus_petite_difference_gauche:
                        Premiere_Partie_gauche[Plus_petite_difference_gauche[3]] = (f"{Plus_petite_difference_gauche[2]} {Plus_petite_difference_gauche[1]}", Plus_petite_difference_gauche[4], Plus_petite_difference_gauche[5])
                
                Premiere_partie_triee_gauche = sorted(Premiere_Partie_gauche, key=lambda x: x[1])
                current_xml_dict_gauche[xml_file_name]["First Name"] = Premiere_partie_triee_gauche # [content, vpos, hpos]

            # Droite
            if len(Premiere_Partie_droite) == 0 or len(Deuxieme_Partie_droite) == 0:
                pass
            else :  
                for a,element in enumerate(Deuxieme_Partie_droite):
                    abs_Plus_petite_difference_droite = abs(Deuxieme_Partie_droite[0][1] - Premiere_Partie_droite[0][1])
                    Plus_petite_difference_droite = [abs_Plus_petite_difference_droite,  Deuxieme_Partie_droite[0][0], Premiere_Partie_droite[0][0], 0, Premiere_Partie_droite[0][1],Premiere_Partie_droite[0][2]]
                    for i,name in enumerate(Premiere_Partie_droite):
                        abs_name_element_droite = abs(element[1] - name[1])
                        if abs_name_element_droite < Plus_petite_difference_droite[0]:
                            Plus_petite_difference_droite = [abs_name_element_droite, element[0], name[0], i, name[1], name[2]] # = [chiffre, prenom, prenom, chiffre, vpos, hpos]
                    
                    if element[0] in Plus_petite_difference_droite:
                        Premiere_Partie_droite[Plus_petite_difference_droite[3]] = (f"{Plus_petite_difference_droite[2]} {Plus_petite_difference_droite[1]}", Plus_petite_difference_droite[4], Plus_petite_difference_droite[5])
                
                Premiere_partie_triee_droite = sorted(Premiere_Partie_droite, key=lambda x: x[1])
                current_xml_dict_droite[xml_file_name]["First Name"] = Premiere_partie_triee_droite # [content, vpos, hpos]

# Partie 3 - Restitution du lien entre Prénom et Nom de Famille gauche et droite
            FirstName_str_gauche = current_xml_dict_gauche.get(xml_file_name).get("First Name")
            LastName_str_gauche = current_xml_dict_gauche.get(xml_file_name).get("Last Name")

            FirstName_str_droite = current_xml_dict_droite.get(xml_file_name).get("First Name")
            LastName_str_droite = current_xml_dict_droite.get(xml_file_name).get("Last Name")

            # Création d'une liste de liste. chaque lst contient : le nom du fichier xml, ?, le prénom, la valeur vpos(y), la valeur hpos(x)
            # Gauche et droite

            FirstName_LastName_gauche = []
            for i, name in enumerate(FirstName_str_gauche):
                FirstName_LastName_gauche.append([xml_file_name, "?", name[0], name[1], name[2]])
                FirstName_LastName_sorted_gauche= sorted(FirstName_LastName_gauche, key=lambda x: x[3])
            
            FirstName_LastName_droite = []
            for i, name in enumerate(FirstName_str_droite):
                FirstName_LastName_droite.append([xml_file_name, "?", name[0], name[1], name[2]])
                FirstName_LastName_sorted_droite = sorted(FirstName_LastName_droite, key=lambda x: x[3])

            # Comparaison des valeurs vpos(y) de chaque élément de First Name et Last Name pour recréer le lien entre le prénom et le nom de famille
            # Gauche
            if len(FirstName_str_gauche) == 0:
                pass
            else : 
                for a, lastname in enumerate(LastName_str_gauche):
                    abs_difference_gauche = abs(FirstName_LastName_sorted_gauche[0][3]-lastname[1])
                    difference_gauche = [abs_difference_gauche,  FirstName_LastName_sorted_gauche[0][2], LastName_str_gauche[0][0], 0, FirstName_LastName_sorted_gauche[0][3]]
                    
                    for i, name in enumerate(FirstName_LastName_sorted_gauche):
                        abs_lastname_name_gauche = abs(lastname[1] - name[3])
                        if abs_lastname_name_gauche <= difference_gauche[0]:
                            difference_gauche = [abs_lastname_name_gauche, lastname[0], name[3], i, name[3]]  

                    if lastname[0] in difference_gauche:
                        FirstName_LastName_gauche[difference_gauche[3]][1]=lastname[0]

            # Droite
            if len(FirstName_str_droite) == 0:
                pass
            else : 
                for a, lastname in enumerate(LastName_str_droite):
                    abs_difference_droite = abs(FirstName_LastName_sorted_droite[0][3]-lastname[1])
                    difference_droite = [abs_difference_droite,  FirstName_LastName_sorted_droite[0][2], LastName_str_droite[0][0], 0, FirstName_LastName_sorted_droite[0][3]]
                    
                    for i, name in enumerate(FirstName_LastName_sorted_droite):
                        abs_lastname_name_droite = abs(lastname[1] - name[3])
                        if abs_lastname_name_droite <= difference_droite[0]:
                            difference_droite = [abs_lastname_name_droite, lastname[0], name[3], i, name[3]]  

                    if lastname[0] in difference_droite:
                        FirstName_LastName_droite[difference_droite[3]][1]=lastname[0]

            # Attriubution a l'output final d'une liste organisée ainsi : le nom du fichier xml, le nom de famille, le prénom, la valeur vpos(y), la valeur hpos(x)
            # Il a été choisi d'attribuer un nom de famille à chaque prénom (et l'inverse), car les prénoms sont plus complets que les noms de famille. Si un prénom n'a pas de nom de famille, le nom de famille est remplacé par un ? 
            output_list_gauche.append(FirstName_LastName_gauche)
            output_list_droite.append(FirstName_LastName_droite)

# Partie 4 - Transformation des données en fichier CSV 
for lst in output_list_gauche:
    for elements in lst:
        elements.insert(1,"Left")

for lst in output_list_droite:
    for elements in lst:
        elements.insert(1,"Right")

output_list.append(output_list_gauche)
output_list.append(output_list_droite)

output_forCSV =[]
for g_ou_d in output_list:
    for xml in g_ou_d: 
        for line in xml:
            output_forCSV.append(line)

output_forCSV.sort(key=lambda x: (x[0], x[1], x[4]))
header = ['File', 'Side', 'Last Name', 'First', 'YPos', 'XPos']

with open("Output1829.csv", "w", newline='',encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    csv_writer.writerows(output_forCSV)
