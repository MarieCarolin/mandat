import lxml.etree as ET
import glob
import os.path
import csv

known = []
# Chemin vers les fichiers XML
for file in glob.glob("test_valais_1970/*.xml"):
    try:
        xml = ET.parse(file)
        cols = []
        # Récupération des colonnes
        for idx, tb in enumerate(xml.xpath("//a:TextBlock[@TAGREFS='TYPE_2'][.//a:TextLine]", namespaces={"a": "http://www.loc.gov/standards/alto/ns-v4#"})):
            # Ne prendre que les 3 premières colonnes trouvées
            if idx > 3:
                break
            cols.append([])
            # Pour chaque ligne de la colonne, l'ajouter
            for line in tb.xpath(".//a:TextLine", namespaces={"a": "http://www.loc.gov/standards/alto/ns-v4#"}):
                cols[-1].append(
                    " ".join([tok for tok in line.xpath("./a:String/@CONTENT", namespaces={"a": "http://www.loc.gov/standards/alto/ns-v4#"})])
                )
        # Trouver la colonne la plus longue
        col_length = [len(c) for c in cols]
        max_length = max(col_length)
        # Rendre l'ensemble des colonnes trouvées de même longueur
        cols = [
            col + (max_length - length) * [""]
            for col, length in zip(cols, col_length)
        ]

        cols = [
            [
                "File",
                os.path.splitext(os.path.basename(file))[0]
            ] + [""] * max(len(cols)-2, 0),# Ajout d'un en-tête identifiant le fichier
            *zip(*cols), # Transposition des colonnes en ligne
            [""] *len(cols), # Ajout d'une ligne CSV vide
        ]
        # Ajout au document général
        known.extend(cols)
    except Exception as E:
        print(file)


with open("test_1870_names.csv", "w") as f:
    csv.writer(f).writerows(known)

"""Bugged files
test_valais_1970/AEV_3090_1870_Sion_Arbaz_003.xml
test_valais_1970/AEV_3090_1870_Sierre_Granges_001.xml
test_valais_1970/AEV_3090_1870_Martigny_Leytron_004.xml
test_valais_1970/AEV_3090_1870_Monthey_Monthey_382.xml
test_valais_1970/AEV_3090_1870_Sion_Arbaz_017.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Salvan_289.xml
test_valais_1970/AEV_3090_1870_Conthey_Nendaz_319.xml
test_valais_1970/AEV_3090_1870_Monthey_Monthey_374.xml
test_valais_1970/AEV_3090_1870_Sierre_Chermignon_008.xml
test_valais_1970/AEV_3090_1870_Sierre_Chermignon_035.xml
test_valais_1970/AEV_3090_1870_Visp_Zeneggen_027.xml
test_valais_1970/AEV_3090_1870_Sierre_Lens_082.xml
test_valais_1970/AEV_3090_1870_Sierre_Montana_003.xml
test_valais_1970/AEV_3090_1870_Brig_Ried_060.xml
test_valais_1970/AEV_3090_1870_Martigny_Martigny-Bourg_017.xml
test_valais_1970/AEV_3090_1870_Martigny_Leytron_077.xml
test_valais_1970/AEV_3090_1870_Sion_Arbaz_049.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Salvan_337.xml
test_valais_1970/AEV_3090_1870_Brig_Brig_095.xml
test_valais_1970/AEV_3090_1870_Sion_Sion_Glaviney_162.xml
test_valais_1970/AEV_3090_1870_Monthey_Collombey-Muraz_022.xml
test_valais_1970/AEV_3090_1870_Sion_Arbaz_009.xml
test_valais_1970/AEV_3090_1870_Sierre_Randogne_034.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Salvan_354.xml
test_valais_1970/AEV_3090_1870_Entremont_Orsieres_050.xml
test_valais_1970/AEV_3090_1870_Sion_Arbaz_001.xml
test_valais_1970/AEV_3090_1870_Sierre_Sierre_135.xml
test_valais_1970/AEV_3090_1870_Sion_Arbaz_084.xml
test_valais_1970/AEV_3090_1870_Monthey_Monthey_338.xml
test_valais_1970/AEV_3090_1870_Brig_Birgisch_027.xml
test_valais_1970/AEV_3090_1870_Sierre_Chermignon_090.xml
test_valais_1970/AEV_3090_1870_Sierre_Sierre_075.xml
test_valais_1970/AEV_3090_1870_Goms_Obergesteln_023.xml
test_valais_1970/AEV_3090_1870_Entremont_Bagnes_Chable_099.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Salvan_292.xml
test_valais_1970/AEV_3090_1870_Brig_Gondo-Zwischbergen_004.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Finhaut_012.xml
test_valais_1970/AEV_3090_1870_Conthey_Vetroz_093.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Salvan_286.xml
test_valais_1970/AEV_3090_1870_Sierre_Sierre_281.xml
test_valais_1970/AEV_3090_1870_Martigny_Riddes_031.xml
test_valais_1970/AEV_3090_1870_Brig_Glis_119.xml
test_valais_1970/AEV_3090_1870_Martigny_Leytron_006.xml
test_valais_1970/AEV_3090_1870_Sierre_Chermignon_076.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Salvan_332.xml
test_valais_1970/AEV_3090_1870_Martigny_Charrat_002.xml
test_valais_1970/AEV_3090_1870_Conthey_Chamoson_161.xml
test_valais_1970/AEV_3090_1870_Goms_Obergesteln_037.xml
test_valais_1970/AEV_3090_1870_Monthey_Monthey_361.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Finhaut_040.xml
test_valais_1970/AEV_3090_1870_Goms_Obergesteln_017.xml
test_valais_1970/AEV_3090_1870_Monthey_Monthey_281.xml
test_valais_1970/AEV_3090_1870_Entremont_Orsieres_311.xml
test_valais_1970/AEV_3090_1870_Herens_Heremence_006.xml
test_valais_1970/AEV_3090_1870_Sierre_Chermignon_079.xml
test_valais_1970/AEV_3090_1870_St-Maurice_Finhaut_023.xml
test_valais_1970/AEV_3090_1870_Goms_Obergesteln_029.xml
test_valais_1970/AEV_3090_1870_Sierre_Chermignon_042.xml
test_valais_1970/AEV_3090_1870_Goms_Obergesteln_015.xml
test_valais_1970/AEV_3090_1870_Entremont_Orsieres_077.xml
test_valais_1970/AEV_3090_1870_Sion_Sion_Glaviney_082.xml
"""