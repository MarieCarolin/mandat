# Ce code permet de restituer les contenus des pages des recensements valaisans de 1837 en fichier CSV
# il y a 6 parties dans ce code :
# 1. Utilisation du clustering pour séparer le contenu en deux colonnes : Prénom, Nom de Famille
# 2. Restitution des prénoms composés dans First Name
# 3. Restitution du lien entre Prénom et Nom de Famille
# 4. Corrections des problèmes de clustering sur certaines pages 
# 5. Corrections spécifiques pour Val d'Illiez et Hermence
# 6. Transformation des données en fichier CSV 

import os
import re
import xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
import numpy as np
from sklearn.cluster import KMeans
import csv

# Chemins vers les dossiers contenant les fichiers XML et JPG.
transcription_folder = 'transcription'
sets_folder = 'Sets'

# lsts
output_list = [] #output final
valeurMedian_HPOS_LastName = [] #lst utilisée pour définir la valeur médiane des positions X des prénoms
valeurs_Cluster_3 = [] #lst utilisée, dans partie 5, pour rectifier les erreurs engendrées par un cluster 3 confondu dans colonne 2
valeurs_Cluster_2 = [] #lst utilisée, dans partie 5, pour rectifier les erreurs engendrées par un cluster 3 confondu dans colonne 2
Valeurs_len_LastName = [] #lst utilisée, dans partie 5, pour rectifier les erreurs engendrées lorsque qu'un cluster 2 prend les données de la colonne prénom et nom
Pages_sans_text = ['AEV_3090_1837_St-Maurice_St-Maurice_037.xml', 'AEV_3090_1837_St-Maurice_St-Maurice_047.xml'] #lst de pages sans texte 
# Partie 1 - Utilisation du clustering pour séparer le contenu en deux colonnes : First Name, Last Name
# Itère sur les sous-dossiers dans le dossier "transcription" 
for subfolder_name in os.listdir(transcription_folder):
    # Construction des chemins vers les dossiers actuels de la boucle
    xml_folder = os.path.join(transcription_folder, subfolder_name)
    img_folder = os.path.join(sets_folder, subfolder_name)

    # Itère sur tous les fichiers xml dans le sous-dossiers actuel de la boucle 
    for xml_file_name in os.listdir(xml_folder):
        if xml_file_name.endswith('.xml') and xml_file_name not in Pages_sans_text:
            print(xml_file_name)
            # Construction du chemin pour le fichier XML actuel dans la boucle, ainsi que le fichier JPG
            xml_file_path = os.path.join(xml_folder, xml_file_name)
            img_file_path = os.path.join(img_folder, xml_file_name.replace('.xml', '.jpg'))

            # Calculer la valeur de la moitié de l'image
            img = Image.open(img_file_path)
            image_width = img.width
            moitie_image = image_width / 2

            # Permet de lire et analyser des fichiers XML
            # Détecte l'élément racine, puis navigue dans l'arborescence XML
            tree = ET.parse(xml_file_path)
            root = tree.getroot()

            # Création d'une liste de tous les éléments XML avec la balise <alto:String>
            namespace = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}
            string_elements = root.findall('.//alto:String', namespace)

            # Extraire les valeurs HPOS et VPOS, les convertir en entiers et les remodeler en un tableau 2D.
            hpos_values = np.array([int(string_element.get('HPOS', 0)) for string_element in string_elements])
            vpos_values = np.array([int(string_element.get('VPOS', 0)) for string_element in string_elements])

            hpos_values = hpos_values.reshape(-1, 1)
            vpos_values = vpos_values.reshape(-1, 1)

            # Définir un nombre de cluster
            num_clusters = 4

            # Appliquer un clustering KMeans basé sur les valeurs HPOS
            kmeans_hpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_hpos = kmeans_hpos.fit_predict(hpos_values)

            # Appliquer un clustering KMeans basé sur les valeurs VPOS
            kmeans_vpos = KMeans(n_clusters=num_clusters, random_state=42)
            clusters_vpos = kmeans_vpos.fit_predict(vpos_values)

            # Calcul de la mediane des valeurs HPOS pour chaque Cluster
            median_values = []
            for i in range(num_clusters):
                cluster_points_hpos = hpos_values[clusters_hpos == i]
                cluster_points_vpos = vpos_values[clusters_vpos == i]
                median_hpos_value = int(np.median(cluster_points_hpos))
                median_vpos_value = int(np.median(cluster_points_vpos))
                median_values.append((i, median_hpos_value, median_vpos_value))

            # Organise le contenu des fichiers XML en fonction de leur appartenance au cluster
            sorted_clusters = sorted(median_values, key=lambda x: x[1])
            valeurs_Cluster_3.append(sorted_clusters[2][1]) 
            valeurs_Cluster_2.append(sorted_clusters[1][1])
            cluster_content = {i: [] for i in range(num_clusters)}

            # Enregistre les valeurs de HPOS et VPOS dans des variables
            for i, string_element in enumerate(string_elements):
                content = string_element.get('CONTENT')
                hpos_str = string_element.get('HPOS')
                if hpos_str is not None: # Contrôle la valeur de HPOS : si elle est None (nulle), c'est une erreur d'OCR ; on lui attribue une valeur de 0
                    hpos = int(hpos_str)
                else:
                    hpos = 0

                vpos_str = string_element.get('VPOS')
                if vpos_str is not None: # Contrôle la valeur de HPOS : si elle est None (nulle), c'est une erreur d'OCR ; on lui attribue une valeur de 0
                    vpos = int(vpos_str)
                else:
                    vpos = 0

                assigned_cluster_hpos = clusters_hpos[i]
                assigned_cluster_vpos = clusters_vpos[i]
                cluster_content[assigned_cluster_hpos].append((hpos, vpos, content))

            # Distribution des éléments dans chaque cluster
            for i in range(num_clusters):
                cluster_content[i] = sorted(cluster_content[i], key=lambda x: x[0])

            # Ajoute chaque élément du cluster dans cluster_dict
            current_xml_dict = {xml_file_name: {'Last Name': [], 'First Name': [], 'Other': []}}
            cluster_names = {1: 'Last Name', 2: 'First Name', 3: 'Other'} # Dictionnaire est organisé ainsi : XML file, Last Name, First Name, Other
            for i, cluster_data in enumerate(sorted_clusters, start=1):
                cluster_index, _, _ = cluster_data
                cluster_content_data = [(hpos, vpos, content) for hpos, vpos, content in cluster_content[cluster_index]]
                cluster_content_data.sort(key=lambda x: x[1]) # Organise les éléments dans chaque cluster. Ensuite, les éléments sont triés selon vpos 

                # Nettoyage des données, puis rangement des données dans le dictionnaire
                for hpos, vpos, content in cluster_content_data:
                    if hpos > moitie_image or content in [" ", "/", "-"] or re.match(r'.*\d+.*', content) or re.match(r'[A-Z]{3,}', content):
                        pass
                    else:
                        if i != 4:
                            current_xml_dict[xml_file_name][cluster_names[i]].append((content, vpos, hpos))
                        else:
                            current_xml_dict[xml_file_name][cluster_names[3]].append((content, vpos, hpos))

            Valeurs_len_LastName.append(len(current_xml_dict.get(xml_file_name).get("Last Name")))
# Partie 2 - Restitution des prénoms composés dans la colonne Prénom
            # Calcul de la médiane des valeurs HPOS pour les Prénoms
            FirstName_str = current_xml_dict.get(xml_file_name).get("First Name")
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
            
            # Attribution de chaque élément de la deuxième partie à un prénom de la première partie en fonction de VPOS (position verticale).
            # Le code parcourt chaque élément de la première partie et compare les valeurs VPOS (y).            
            for a,element in enumerate(Deuxieme_Partie):
                abs_Plus_petite_difference = abs(Deuxieme_Partie[0][1] - Premiere_Partie[0][1])
                Plus_petite_difference = [abs_Plus_petite_difference,  Deuxieme_Partie[0][0], Premiere_Partie[0][0], 0, Premiere_Partie[0][1],Premiere_Partie[0][2]]
                for i,name in enumerate(Premiere_Partie):
                    abs_name_element = abs(element[1] - name[1])
                    if abs_name_element < Plus_petite_difference[0]:
                        Plus_petite_difference = [abs_name_element, element[0], name[0], i, name[1], name[2]] # = [chiffre, prenom, prenom, chiffre, vpos, hpos]
                
                if element[0] in Plus_petite_difference:
                    Premiere_Partie[Plus_petite_difference[3]] = (f"{Plus_petite_difference[2]} {Plus_petite_difference[1]}", Plus_petite_difference[4], Plus_petite_difference[5])
            
            Premiere_partie_triee = sorted(Premiere_Partie, key=lambda x: x[1])
            current_xml_dict[xml_file_name]["First Name"] = Premiere_partie_triee # [content, vpos, hpos]

# Partie 3 - Restitution du lien entre Prénom et Nom de Famille 
            FirstName_str = current_xml_dict.get(xml_file_name).get("First Name")
            LastName_str = current_xml_dict.get(xml_file_name).get("Last Name")

            # Création d'une liste de liste. chaque lst contient : le nom du fichier xml, ?, le prénom, la valeur vpos(y), la valeur hpos(x)
            FirstName_LastName=[]
            for i, name in enumerate(FirstName_str):
                FirstName_LastName.append([xml_file_name, "?", name[0], name[1], name[2]])
                FirstName_LastName_sorted= sorted(FirstName_LastName, key=lambda x: x[3])

            # Comparaison des valeurs vpos(y) de chaque élément de First Name et Last Name pour recréer le lien entre le prénom et le nom de famille
            for a, lastname in enumerate(LastName_str):
                abs_difference = abs(FirstName_LastName_sorted[0][3]-lastname[1])
                difference = [abs_difference,  FirstName_LastName_sorted[0][2], LastName_str[0][0], 0, FirstName_LastName_sorted[0][3]]
                
                for i, name in enumerate(FirstName_LastName_sorted):
                    abs_lastname_name = abs(lastname[1] - name[3])
                    if abs_lastname_name <= difference[0]:
                        difference = [abs_lastname_name, lastname[0], name[3], i, name[3]]  

                if lastname[0] in difference:
                    FirstName_LastName[difference[3]][1]=lastname[0]

            # Attriubution à l'output final d'une liste organisée ainsi : le nom du fichier xml, le nom de famille, le prénom, la valeur vpos(y), la valeur hpos(x)
            # Il a été choisi d'attribuer un nom de famille à chaque prénom (et l'inverse), car les prénoms sont plus complets que les noms de famille. Si un prénom n'a pas de nom de famille, le nom de famille est remplacé par un ?
            output_list.append(FirstName_LastName) # [xml file, nom, prénom, vpos, hpos]
            

# Partie 4 - Correction des problèmes de clustering sur certaines pages 
# Le problème de clustering est dû à un décalage des colonnes
# Pour résoudre ce problème, une médiane des valeurs HPOS (x) des Prénoms de l'ensemble du corpus est calculée comme référence
# Si la médiane des valeurs HPOS des Prénoms dans un fichier XML s'éloigne de la valeur de référence, elle est isolée.
# Une fois isolée, un autre code est exécuté en prenant en compte le décalage des colonnes.

# Calcul de la médiane référence
output_village=[]
lst_clustervillage = []
for firstname in output_list:
    for firstnamehpos in firstname:
        valeurMedian_HPOS_LastName.append(firstnamehpos[4])

valeurMedian_HPOS_LastName_Array = np.array(valeurMedian_HPOS_LastName)
valeurMedian_HPOS_LastName_Array_median = np.median(valeurMedian_HPOS_LastName_Array)

# Calcul de l'écart médian
Ecart_Median_LastName = []
for firstname in output_list:
    for firstnamehpos in firstname:
        Valeur_absolue_Ecart = abs(valeurMedian_HPOS_LastName_Array_median - firstnamehpos[4])
        Ecart_Median_LastName.append(Valeur_absolue_Ecart)

len_Ecart_Median_LastName = len(Ecart_Median_LastName)
Ecart_Median_LastName_Array = np.array(Ecart_Median_LastName)
Ecart_Median_LastName_Absolu = np.sum(Ecart_Median_LastName_Array)/len_Ecart_Median_LastName
Ecart_Median_Absolu_PLUS_Median_LastName = Ecart_Median_LastName_Absolu + valeurMedian_HPOS_LastName_Array_median
Ecart_Median_Absolu_PLUS_Median_LastName_2fois = 2*Ecart_Median_LastName_Absolu + valeurMedian_HPOS_LastName_Array_median

# Calcul la mediane pour chaque page et place les noms des XML a isolés dans la liste lst_clustervillage
for firstname in output_list:
    hpos_values_int = []
    for firstnamehpos in firstname:
        hpos_values_int.append(firstnamehpos[4])

    hposvaluearray_int = np.array(hpos_values_int)
    hposmedian_int = np.median(hposvaluearray_int)
    if hposmedian_int > Ecart_Median_Absolu_PLUS_Median_LastName_2fois:
        if firstnamehpos[0] not in lst_clustervillage:
            lst_clustervillage.append(firstnamehpos[0])

# Iteration du code pour effectuer les partie 1, 2 et 3 sur les XML isolés  
for subfolder_name in os.listdir(transcription_folder):
    xml_folder_village = os.path.join(transcription_folder, subfolder_name)
    img_folder_village = os.path.join(sets_folder, subfolder_name)
    for xml_file_name in os.listdir(xml_folder_village):
        if xml_file_name.endswith('.xml') and xml_file_name in lst_clustervillage :
            xml_file_path_village = os.path.join(xml_folder_village, xml_file_name)
            img_file_path_village = os.path.join(img_folder_village, xml_file_name.replace('.xml', '.jpg'))

            tree_village = ET.parse(xml_file_path_village)
            root_village = tree_village.getroot()
            namespace_village = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}
            
            elements_xml =[]
            string_elements_village = root_village.findall('.//alto:String', namespace_village) 
            
            # Calcul la médiane des valeurs hpos pour le XML actuel 
            # Si un élément s'en éloigne trop, il est à éliminer des éléments à traiter 
            median_hpos = []
            for string in string_elements_village:
                content = string.get('CONTENT')
                hpos = string.get('HPOS')
                vpos = string.get('VPOS')
                median_village = int(valeurMedian_HPOS_LastName_Array_median)
                median_ecart_village = int(Ecart_Median_Absolu_PLUS_Median_LastName)
                if hpos is not None:
                    hpos_int = int(hpos)
                else:
                    hpos_int = 0

                if vpos is not None:
                    vpos_int = int(vpos)
                else:
                    vpos_int = 0

                ecart_mediane_village = abs(hpos_int - median_village)
                ecart_ecart_mediane_village = abs(hpos_int - median_ecart_village)
                if ecart_ecart_mediane_village > ecart_mediane_village and content not in [" ", "/", "-"] and not re.match(r'.*\d+.*', content) and not re.match(r'[A-Z]{3,}', content):
                    elements_xml.append([content,hpos_int,vpos_int]) 

            # Variation de l'étape 1, pas de tri avec kmean, mais en fonction de la médiane des hpos(x) des éléments
            FirstName = []
            LastName = []
            median_hpos = []
            for hpos in elements_xml :
                median_hpos.append(hpos[1])

            median_hpo_array = np.array(median_hpos)
            median_hpo_page = np.median(median_hpo_array)

            Ecart_Median_village = []
            for hpos in elements_xml:
                Valeur_absolue_Ecart_village = abs(median_hpo_page - hpos[1])
                Ecart_Median_village.append(Valeur_absolue_Ecart_village)

            len_Ecart_Median_village = len(Ecart_Median_village)
            Ecart_Median_Array_village = np.array(Ecart_Median_village)
            Ecart_Median_Absolu_village = np.sum(Ecart_Median_Array_village)/len_Ecart_Median_village

            for hpos in elements_xml :
                if hpos[1] >= Ecart_Median_Absolu_village:
                    FirstName.append(hpos)
                else:
                    LastName.append(hpos)

            # Etape 2
            FirstName_Hpos_village = []
            for hpos in FirstName:
                FirstName_Hpos_village.append((hpos[1]))
            
            FirstName_Hpos_array_village = np.array(FirstName_Hpos_village)
            FirstName_Hpos_median_village = np.median(FirstName_Hpos_array_village)

            Ecart_Median_FirstName_village = []
            for hpos in FirstName_Hpos_village:
                Valeur_absolue_Ecart__firstName_village = abs(FirstName_Hpos_median_village - hpos)
                Ecart_Median_FirstName_village.append(Valeur_absolue_Ecart__firstName_village)

            len_Ecart_Median_firstname_village = len(Ecart_Median_FirstName_village)
            Ecart_Median_FirstName_village_array = np.array(Ecart_Median_FirstName_village)
            Ecart_Median_Absolu_firstname_village = np.sum(Ecart_Median_FirstName_village_array)/len_Ecart_Median_firstname_village
            Ecart_Median_Absolu_PLUS_Median_firstname_village = Ecart_Median_Absolu_firstname_village + FirstName_Hpos_median_village
            
            Premiere_Partie_village = []
            Deuxieme_Partie_village =[]
            for firstname in FirstName:
                Ecart_Hpos_Mediane_village = abs(FirstName_Hpos_median_village - firstname[1])
                Ecart_Hpos_Median_Absolu_PLUS_Median_firstname_village = abs(Ecart_Median_Absolu_PLUS_Median_firstname_village - firstname[1])
                if Ecart_Hpos_Mediane_village < Ecart_Hpos_Median_Absolu_PLUS_Median_firstname_village: 
                    Premiere_Partie_village.append(firstname)
            
                else :  
                    Deuxieme_Partie_village.append(firstname)

            for element in Deuxieme_Partie_village:
                abs_Plus_petite_difference_village = abs(Deuxieme_Partie_village[0][2] - Premiere_Partie_village[0][2])
                Plus_petite_difference_village = [abs_Plus_petite_difference_village,  Deuxieme_Partie_village[0][0], Premiere_Partie_village[0][0], 0, Premiere_Partie_village[0][1],Premiere_Partie_village[0][2]]
                for i,name in enumerate(Premiere_Partie_village):
                    abs_name_element_village = abs(element[2] - name[2])
                    if abs_name_element_village < Plus_petite_difference_village[0]:
                        Plus_petite_difference_village = [abs_name_element_village, element[0], name[0], i, name[1], name[2]]
                
                if element[0] in Plus_petite_difference_village:
                    Premiere_Partie_village[Plus_petite_difference_village[3]] = (f"{Plus_petite_difference_village[2]} {Plus_petite_difference_village[1]}", Plus_petite_difference_village[4], Plus_petite_difference_village[5])
            
            Premiere_partie_triee_village = sorted(Premiere_Partie_village, key=lambda x: x[2])
            FirstName = Premiere_partie_triee_village

            # Etape 3
            FirstName_LastName_village=[]
            for i, name in enumerate(FirstName):
                FirstName_LastName_village.append([xml_file_name, "?", name[0], name[1], name[2]]) 
                FirstName_LastName_village_sorted= sorted(FirstName_LastName_village, key=lambda x: x[4])

            for a, lastname in enumerate(LastName):
                abs_difference_village = abs(FirstName_LastName_village_sorted[0][3]-lastname[1])
                difference_village = [abs_difference_village,  FirstName_LastName_village_sorted[0][2], LastName[0][0], 0, FirstName_LastName_village_sorted[0][4]]
                for i, name in enumerate(FirstName_LastName_village_sorted):

                    abs_lastname_name_village = abs(lastname[2] - name[4])
                    if abs_lastname_name_village <= difference_village[0]:
                        difference_village = [abs_lastname_name_village, lastname[0], name[4], i, name[4]]  

                if lastname[0] in difference_village:
                    FirstName_LastName_village[difference_village[3]][1]=lastname[0]
            
            output_village.append(FirstName_LastName_village)

# Modification de l'output final avec output_village
for xml in output_list:
    for line in xml:
        if line[0] in lst_clustervillage: 
            output_list.remove(xml)
            break

for xml in output_village:
    output_list.append(xml)

# Partie 5 - Corrections pour Val d'Illiez et Hermence
# Les clusters des pages d'Héremence et Val d'Illiez sont décallées à cause des notations de filliation "filles", "fils", "femme", etc

output_HER_VAL = []   
output_list_int__HER_VAL =[] 
for xml_file_name in os.listdir(xml_folder):
    print(xml_file_name)
    if xml_file_name.endswith('.xml') : 
        if re.match(r'AEV_3090_1837_Herens_Heremence_\d+', xml_file_name) or re.match(r'AEV_3090_1837_Monthey_Val_d_Illiez_\d+', xml_file_name):
            xml_file_path_HER_VAL = os.path.join(xml_folder, xml_file_name)
            tree_HER_VAL = ET.parse(xml_file_path_HER_VAL)
            root_HER_VAL = tree_HER_VAL.getroot()

            namespace_HER_VAL = {'alto': 'http://www.loc.gov/standards/alto/ns-v4#'}
            string_elements_HER_VAL = root_HER_VAL.findall('.//alto:String', namespace_HER_VAL)
            
            # Nettoyer les données et les organisées dans une liste
            lst_string_elements = []
            for string in string_elements_HER_VAL:
                content_HER_VAL = string.get('CONTENT')
                hpos_HER_VAL = string.get('HPOS')
                vpos_HER_VAL = string.get('VPOS')
                if content_HER_VAL not in ["son", "sa", "se", "la", "le", "fils", "fille", "femme", "file","fil", "fi", "filie","fis", "fos","fo","Sufille", "Tente", "frere", "loeur", "fem", "filleid", "femn", "femmed", "fillled", "femne", '"fis'] :
                    lst_string_elements.append([xml_file_name, content_HER_VAL, vpos_HER_VAL,hpos_HER_VAL])
            
            output_HER_VAL.append(lst_string_elements)

# Créer les clusters à partir des données nettoyées
for xml_file in output_HER_VAL:
    xml_file_name_HER_VAL = xml_file[0][0]

    img_file_path_HER_VAL = os.path.join(img_folder, xml_file_name_HER_VAL.replace('.xml', '.jpg'))
    img_HER_VAL = Image.open(img_file_path_HER_VAL)
    image_width_HER_VAL = img_HER_VAL.width
    moitie_image_HER_VAL = image_width_HER_VAL / 2
    
    hpos_values_HER_VAL = []
    for string in xml_file:
        hpos_values_HER_VAL.append(int(string[3]))

    hpos_values_HER_VAL_array = np.array(hpos_values_HER_VAL)
    hpos_values_HER_VAL_array = hpos_values_HER_VAL_array.reshape(-1, 1)
    num_clusters_HER_VAL = 4

    kmeans_hpos_HER_VAL = KMeans(n_clusters=num_clusters_HER_VAL, random_state=42)
    clusters_hpos_HER_VAL = kmeans_hpos_HER_VAL.fit_predict(hpos_values_HER_VAL_array)

    median_values_HER_VAL = []
    for i in range(num_clusters_HER_VAL):
        cluster_points_hpos_HER_VAL = hpos_values_HER_VAL_array[clusters_hpos_HER_VAL == i]
        median_hpos_value_HER_VAL = int(np.median(cluster_points_hpos_HER_VAL))
        median_values_HER_VAL.append((i, median_hpos_value_HER_VAL))


    sorted_clusters_HER_VAL = sorted(median_values_HER_VAL, key=lambda x: x[1])
    cluster_content_HER_VAL = {i: [] for i in range(num_clusters_HER_VAL)}

    # Correction des pages où les clusters 2 et 3 sont tous les deux reconnus dans la colonne des Prénoms
    # Calcul de l'éloignement moyen entre le cluster 2 et le cluster 3
    # Si l'éloignement est significatif vers le bas, alors le contenu du cluster 3 appartient au cluster 2
    valeurs_Cluster_3_array = np.array(valeurs_Cluster_3)
    valeurs_Cluster_2_array = np.array(valeurs_Cluster_2)

    diff_Cluster2_3 = []
    for i, hpos_2 in enumerate(valeurs_Cluster_2_array) :
        diff = abs(valeurs_Cluster_3_array[i]-hpos_2)
        diff_Cluster2_3.append(diff)

    diff_Cluster2_3_array = np.array(diff_Cluster2_3)
    diff_Cluster2_3_median = np.median(diff_Cluster2_3_array)
    
    lst_ecart = []
    for i,hpos in enumerate(valeurs_Cluster_3_array) :
        valeur_ecart = abs(hpos- (valeurs_Cluster_2_array[i]+diff_Cluster2_3_median))
        lst_ecart.append(valeur_ecart)
        
    lst_ecart_array = np.array(lst_ecart)
    Ecart_absolu_3cluster = np.sum(lst_ecart_array)/len(lst_ecart_array)
    posX_limite_Cluster3 = (sorted_clusters_HER_VAL[1][1] + diff_Cluster2_3_median) - Ecart_absolu_3cluster

    # Correction des pages où le cluster 2 prend les données des colonnes nom et prénoms
    # Calcul de la médiane de la quantité de données pour le Nom de Famille (Last Name)
    # Si la quantité est significativement trop grande, alors les données avant le cluster 1 appartiennent à 1, les données après le cluster 2 mais avant le 3 appartiennent à 2
    Valeurs_len_LastName_array = np.array(Valeurs_len_LastName)
    valeur_len_lastName_mediane = np.median(Valeurs_len_LastName_array)

    ecarts_len_lastName_mediane = []
    for valeur in Valeurs_len_LastName_array:
        abs_ecart_mediane= abs(valeur-valeur_len_lastName_mediane)
        ecarts_len_lastName_mediane.append(abs_ecart_mediane)

    ecarts_len_lastName_mediane_array = np.array(ecarts_len_lastName_mediane)
    Ecart_absolu_len_lastName = np.sum(ecarts_len_lastName_mediane_array)/len(ecarts_len_lastName_mediane_array)

    # Ajoute chaque élément des clusters dans current_xml_dict_HER_VAL

    for i,string in enumerate(xml_file):
        content_string = string[1]
        hpos_string = string[3]

        if hpos_string is not None: 
            hpos_HER__VAL = int(hpos_string)
        else:
            hpos_HER__VAL = 0

        vpos_string = string[2]
        if vpos_string is not None: 
            vpos_HER__VAL = int(vpos_string)
        else:
            vpos_HER__VAL = 0

        assigned_cluster_hpos_HER_VAL = clusters_hpos_HER_VAL[i]
        cluster_content_HER_VAL[assigned_cluster_hpos_HER_VAL].append((hpos_HER__VAL, vpos_HER__VAL, content_string))

    for i in range(num_clusters_HER_VAL):
        cluster_content_HER_VAL[i] = sorted(cluster_content_HER_VAL[i], key=lambda x: x[0])

    current_xml_dict_HER_VAL = {xml_file_name_HER_VAL: {'Last Name': [], 'First Name': [], 'Other': []}}
    cluster_names_HER_VAL = {1: 'Last Name', 2: 'First Name', 3: 'Other'}

    for i, cluster_data in enumerate(sorted_clusters_HER_VAL, start=1):
        cluster_index_HER_VAL, _ = cluster_data
        cluster_content_data_HER_VAL = [(hpos, vpos, content) for hpos, vpos, content in cluster_content_HER_VAL[cluster_index_HER_VAL]]
        cluster_content_data_HER_VAL.sort(key=lambda x: x[1]) 

        for hpos, vpos, content in cluster_content_data_HER_VAL:
            if hpos > moitie_image_HER_VAL or content in [" ", "/", "-", "=", "/.", "Â°" ] or re.match(r'.*\d+.*', content) or re.match(r'[A-Z]{3,}', content):
                pass
            else:
                if i == 1 or i == 2:
                    current_xml_dict_HER_VAL[xml_file_name_HER_VAL][cluster_names_HER_VAL[i]].append((content, vpos, hpos))
                if i == 3 :
                    if sorted_clusters_HER_VAL[2][1] < posX_limite_Cluster3 :
                        current_xml_dict_HER_VAL[xml_file_name_HER_VAL][cluster_names_HER_VAL[2]].append((content, vpos, hpos))
                    else :
                        current_xml_dict_HER_VAL[xml_file_name_HER_VAL][cluster_names_HER_VAL[3]].append((content, vpos, hpos))
                if i == 4:
                    current_xml_dict_HER_VAL[xml_file_name_HER_VAL][cluster_names_HER_VAL[3]].append((content, vpos, hpos))

    # Modification du dictionnaire pour les pages dont le cluster 2 prend les données des colonnes nom et prénoms

    if len(current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("Last Name")) > valeur_len_lastName_mediane+Ecart_absolu_len_lastName and len(current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("Last Name")) > len(current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("First Name")) :             
        lst_current_lastName_firstName_value = []
        lst_current_lastName_firstName_value.append(current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("Last Name"))
        lst_current_lastName_firstName_value.append(current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("First Name"))
        
        lst_First_Name_value_HER_VAL = []
        lst_Last_Name_value_HER_VAL = []
        for lst in lst_current_lastName_firstName_value:
            for element in lst:
                if element[2] < sorted_clusters_HER_VAL[0][1]:
                    lst_Last_Name_value_HER_VAL.append(element)
                else :
                    lst_First_Name_value_HER_VAL.append(element)

        current_xml_dict_HER_VAL[xml_file_name_HER_VAL].update({'Last Name': lst_Last_Name_value_HER_VAL})
        current_xml_dict_HER_VAL[xml_file_name_HER_VAL].update({'First Name': lst_First_Name_value_HER_VAL})

    # Partie 2 - Restitution des prénoms composés dans la colonne Prénom
    # Calcul de la médiane des valeurs HPOS pour les Prénoms
    FirstName_str_HER_VAL = current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("First Name")
    len_FirstName_str_HER_VAL = len(FirstName_str_HER_VAL)
    FirstName_Hpos_HER_VAL = []
    for i in range(len_FirstName_str_HER_VAL):
        FirstName_Hpos_HER_VAL.append((FirstName_str_HER_VAL[i][2]))
    
    FirstName_Hpos_array_HER_VAL = np.array(FirstName_Hpos_HER_VAL)
    FirstName_Hpos_median_HER_VAL = np.median(FirstName_Hpos_array_HER_VAL)

    # Calcul de l'écart médian absolu. Cela permet d'obtenir une valeur de référence pour identifier la deuxième partie du nom composé
    Ecart_Median_HER_VAL = []
    for FirstName in FirstName_str_HER_VAL:
        Valeur_absolue_Ecart_HER_VAL = abs(FirstName_Hpos_median_HER_VAL - FirstName[2])
        Ecart_Median_HER_VAL.append(Valeur_absolue_Ecart_HER_VAL)

    len_Ecart_Median_HER_VAL = len(Ecart_Median_HER_VAL)
    Ecart_Median_Array_HER_VAL = np.array(Ecart_Median_HER_VAL)
    Ecart_Median_Absolu_HER_VAL = np.sum(Ecart_Median_Array_HER_VAL)/len_Ecart_Median_HER_VAL
    Ecart_Median_Absolu_PLUS_Median_HER_VAL = Ecart_Median_Absolu_HER_VAL + FirstName_Hpos_median_HER_VAL
    
    # Tri des contenus de la colonne Prénom : Première partie pour les prénoms proches de la médiane, deuxième partie pour les prénoms proches de la médiane + de l'écart absolu
    Premiere_Partie_HER_VAL = []
    Deuxieme_Partie_HER_VAL =[]
    for FirstName in FirstName_str_HER_VAL: 
        Ecart_Hpos_Mediane_HER_VAL = abs(FirstName_Hpos_median_HER_VAL - FirstName[2])
        Ecart_Hpos_Median_Absolu_PLUS_Median_HER_VAL = abs(Ecart_Median_Absolu_PLUS_Median_HER_VAL - FirstName[2])
        if Ecart_Hpos_Mediane_HER_VAL < Ecart_Hpos_Median_Absolu_PLUS_Median_HER_VAL: 
            Premiere_Partie_HER_VAL.append(FirstName)
    
        else :  
            Deuxieme_Partie_HER_VAL.append(FirstName)

    # Attribution de chaque élément de la deuxième partie à un prénom de la première partie en fonction de VPOS (position verticale)
    # Le code parcourt chaque élément de la première partie et compare les valeurs VPOS (y)              
    for a,element in enumerate(Deuxieme_Partie_HER_VAL):
        abs_Plus_petite_difference_HER_VAL = abs(Deuxieme_Partie_HER_VAL[0][1] - Premiere_Partie_HER_VAL[0][1])
        Plus_petite_difference_HER_VAL = [abs_Plus_petite_difference_HER_VAL,  Deuxieme_Partie_HER_VAL[0][0], Premiere_Partie_HER_VAL[0][0], 0, Premiere_Partie_HER_VAL[0][1],Premiere_Partie_HER_VAL[0][2]]
        for i,name in enumerate(Premiere_Partie_HER_VAL):
            abs_name_element_HER_VAL = abs(element[1] - name[1])
            if abs_name_element_HER_VAL < Plus_petite_difference_HER_VAL[0]:
                Plus_petite_difference_HER_VAL = [abs_name_element_HER_VAL, element[0], name[0], i, name[1], name[2]] 
        
        if element[0] in Plus_petite_difference_HER_VAL:
            Premiere_Partie_HER_VAL[Plus_petite_difference_HER_VAL[3]] = (f"{Plus_petite_difference_HER_VAL[2]} {Plus_petite_difference_HER_VAL[1]}", Plus_petite_difference_HER_VAL[4], Plus_petite_difference_HER_VAL[5])
    
    Premiere_partie_triee_HER_VAL = sorted(Premiere_Partie_HER_VAL, key=lambda x: x[1])
    current_xml_dict_HER_VAL[xml_file_name_HER_VAL]["First Name"] = Premiere_partie_triee_HER_VAL 

# Partie 3 - Restituion du lien entre Prénom et Nom de Famille 
    FirstName_str_HER_VAL = current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("First Name")
    LastName_str_HER_VAL = current_xml_dict_HER_VAL.get(xml_file_name_HER_VAL).get("Last Name")

    # Création d'une liste de liste. chaque lst contient : le nom du fichier xml, ?, le prénom, la valeur vpos(y), la valeur hpos(x)
    FirstName_LastName_HER_VAL=[]
    for i, name in enumerate(FirstName_str_HER_VAL):
        FirstName_LastName_HER_VAL.append([xml_file_name_HER_VAL, "?", name[0], name[1], name[2]])
        FirstName_LastName_sorted_HER_VAL= sorted(FirstName_LastName_HER_VAL, key=lambda x: x[3])

    # Comparaison des valeurs vpos(y) de chaque élément de First Name et Last Name pour recréer le lien entre le prénom et le nom de famille
    for a, lastname in enumerate(LastName_str_HER_VAL):
        abs_difference_HER_VAL = abs(FirstName_LastName_sorted_HER_VAL[0][3]-lastname[1])
        difference_HER_VAL = [abs_difference_HER_VAL,  FirstName_LastName_sorted_HER_VAL[0][2], LastName_str_HER_VAL[0][0], 0, FirstName_LastName_sorted_HER_VAL[0][3]]
        
        for i, name in enumerate(FirstName_LastName_sorted_HER_VAL):
            abs_lastname_name_HER_VAL = abs(lastname[1] - name[3])
            if abs_lastname_name_HER_VAL <= difference_HER_VAL[0]:
                difference_HER_VAL = [abs_lastname_name_HER_VAL, lastname[0], name[3], i, name[3]]  

        if lastname[0] in difference_HER_VAL:
            FirstName_LastName_HER_VAL[difference_HER_VAL[3]][1]=lastname[0]

    output_list_int__HER_VAL.append(FirstName_LastName_HER_VAL) # [xml file, nom, prénom, vpos, hpos]

# Modification de l'output final avec output_village
for xml in output_list:
    for line in xml:
        if re.match(r'AEV_3090_1837_Herens_Heremence_\d+', line[0]) or re.match(r'AEV_3090_1837_Monthey_Val_d_Illiez_\d+', line[0]):
            output_list.remove(xml)
            break

for xml in output_list_int__HER_VAL:
    output_list.append(xml)

# Partie 6 - Transformation des données en fichier CSV 
output_forCSV =[]
for xml in output_list:
    for line in xml:
        output_forCSV.append(line)

output_forCSV.sort(key=lambda x: (x[0], x[3]))
header = ['File', 'Last Name', 'First', 'YPos', 'XPos']

with open("Output1837.csv", "w", newline='',encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(header)
    csv_writer.writerows(output_forCSV)