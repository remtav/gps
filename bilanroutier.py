# Ressources:
# https://pyshark.com/geocoding-in-python/
# https://www.donneesquebec.ca/recherche/dataset/rapports-d-accident#

import argparse
import os
import time
from pathlib import Path
import logging
from typing import Union

import geopandas
import numpy as np

import pandas as pd
from geopy.geocoders import GoogleV3
# import googlemaps
# import geocoder

#OUTPUT_PATH = Path("C:\\Users\\tavr1902\\Bilan_routier_carte")
OUTPUT_PATH = Path("./")
DEBUG = True
API = 'YOUR API KEY'


def main(csv_input: Union[Path, str],
         output_path: Union[Path, str] = None,
         debug: bool = False):
    if not output_path:
        output_path = csv_input.parent

    import logging.config
    log_config_path = Path('logging.conf').absolute()
    if not isinstance(output_path, Path):
        output_path = Path(output_path)
    logfile = output_path / f'{csv_input.stem}.log'
    logfile_debug = output_path / f'{csv_input.stem}_debug.log'
    console_level_logging = 'INFO' if not debug else 'DEBUG'
    logging.config.fileConfig(str(log_config_path), defaults={'logfilename': str(logfile),
                                                         'logfilename_debug': str(logfile_debug),
                                                         'console_level': console_level_logging})
    if debug:
        logging.info(f'Debug mode activated')
    logging.info(f'All output files will be written to {output_path}')

    df = pd.read_csv(csv_input)
    df['LATITUDE'] = np.nan
    df['LONGITUDE'] = np.nan
    #print(df)
    # FIXME: Hardcoded to Sherbrooke and at least one pedestrian victim
    logging.info(f'Loaded {csv_input} to pandas dataframe with {df.shape[0]} rows and {df.shape[1]} columns')
    subset = df[(df['MRC'] == "Sherbrooke (43 )") & (df['NB_VICTIMES_PIETON'] > 0)]
    logging.debug(f'Filtered {subset.shape[0]} rows for Sherbrooke with at least one pedestrian as victim')
    #del df

    count_searched = count_found = 0
    for index, row in subset.iterrows():
        # 1. Identification de l'adresse ou de l'intersection de l'accident
        no_civ = rue = None
        # Si un numéro civique est identifié, récupérons la rue de l'accident
        if not row.isnull()['NO_CIVIQ_ACCDN']:
            no_civ = row['NO_CIVIQ_ACCDN']
            rue = row['RUE_ACCDN']
        # Sinon, tentons de démêler l'intersection de l'accident
        else:
            rue1 = rue2 = None
            # Si les champs RUE_ACCDN et ACCDN_PRES_DE contienne une information, ceci sera l'intersection à chercher
            if not row.isnull()['RUE_ACCDN'] and not row.isnull()['ACCDN_PRES_DE']:
                rue1 = row['RUE_ACCDN']
                rue2 = row['ACCDN_PRES_DE']
            # Autrement, si le champ RUE_ACCDN est vide, mais pas ACCDN_PRES_DE, alors nous tenterons de trouver deux
            # noms de rues dans ce second champ en cherchant les caractères " ET " et les rues avant et après ces
            # caractères.
            elif row.isnull()['RUE_ACCDN'] and not row.isnull()['ACCDN_PRES_DE']:
                if ' ET ' in row['ACCDN_PRES_DE']:
                    rue1 = row['ACCDN_PRES_DE'].split(' ET ')[0]
                    rue2 = row['ACCDN_PRES_DE'].split(' ET ')[1]
                # Si on ne trouve pas les caractères " ET ", alors il y a peut-être une adresse dans ce champ. On
                # cherche alors un numéro civique et une rue qui le succède
                else:
                    for word in row['ACCDN_PRES_DE'].split(' '):
                        if word.isdigit():
                            no_civ = word
                            rue = row['ACCDN_PRES_DE'].split(f'{no_civ} ')[1]
            # Autrement et à l'inverse, si le champ ACCDN_PRES_DE est vide, mais pas RUE_ACCDN, alors on répète en
            # inversant ces deux champs.
            elif row.isnull()['ACCDN_PRES_DE'] and not row.isnull()['RUE_ACCDN']:
                if ' ET ' in row['RUE_ACCDN']:
                    rue1 = row['RUE_ACCDN'].split(' ET ')[0]
                    rue2 = row['RUE_ACCDN'].split(' ET ')[1]
                else:
                    for word in row['RUE_ACCDN'].split(' '):
                        if word.isdigit():
                            no_civ = word
                            rue = row['RUE_ACCDN'].split(f'{no_civ} ')
        # 2. On va maintenant géocoder à partir de l'info trouvée ci-dessus

        # D'abord, on construit la chaîne de caractère qui sera soumise aux services de géocodage de Google
        loc_string = None
        if no_civ and rue:
            # FIXME city is harcoded here
            # Je rajoute manuellement ", Sherbrooke, QC", ce qui n'est pas idéal pour la flexibilité du script...
            loc_string = f'{int(no_civ)} {rue}, Sherbrooke, QC'
            print(f'{index}: {loc_string}')
        elif rue1 and rue2:
            loc_string = f'{rue1} & {rue2}, Sherbrooke, QC'
            print(f'{index}: {loc_string}')
        else:
            logging.warning(f"Couldn't parse row at index {index}: {row}")

        # Puis, si l'étape précédente n'échoue pas, on procède au géocodage (merci Google!)
        if loc_string:
            count_searched += 1
            #g = geocoder.google(f'{loc_string}, Sherbrooke, QC')
            #g = geocoder.osm(loc_string)
            #print(g.latlng)

            geolocator = GoogleV3(api_key=API)
            location = geolocator.geocode(loc_string)
            logging.debug(f'Address found: {location.address}\n'
                          f'Coordinates found: {location.latitude}, {location.longitude}')

        if location.latitude: #g.ok:
            #df.at[index, 'LATITUDE'] = g.lat
            #df.at[index, 'LONGITUDE'] = g.lng
            df.at[index, 'LONGITUDE'] = location.longitude
            df.at[index, 'LATITUDE'] = location.latitude
            count_found += 1

    logging.info(f'Total accidents to search: {subset.shape[0]} \n'
                 f'Total locations searched (location successfully parsed): {count_searched}\n'
                 f'Total geocoded: {count_found}')

    # On rassemble toutes les lignes pour lesquelles une longitude et latitude a été trouvée
    subset = df[(df['LATITUDE'].notnull()) & (df['LONGITUDE'].notnull())]
    #logging.debug(subset.head())

    # On prépare les lignes qui seront écrites vers le fichier de sortie en format geopackage
    gdf = geopandas.GeoDataFrame(subset, geometry=geopandas.points_from_xy(subset.LONGITUDE, subset.LATITUDE))
    #logging.debug(gdf.head())
    geofile = output_path / f'rapports_accident.gpkg'
    gdf.to_file(geofile, driver='GPKG', layer=f'{csv_input.stem}')

    # Voilà!

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Geocoding du bilan routier')
    parser.add_argument('BilanCSV', metavar='DIR',
                        help='Chemin vers fichier .csv du bilan routier ou vers répertoire qui contient ce(s) '
                             'fichier(s)')
    args = parser.parse_args()
    input_path = args.ParamFile
    input_path = Path(input_path)
    start_time = time.time()
    print(f'\n\nStarting with {args.ParamFile}\n\n')

    globbed = None
    if input_path.suffix == '.csv':
        main(input_path, output_path=OUTPUT_PATH, debug=DEBUG)
    # Si un répertoire est donné en entrée, on boucle à travers les fichiers .csv qu'il contient
    elif input_path.is_dir():
        globbed = input_path.glob('*git.csv')
        for csv_file in globbed:
            main(csv_file, output_path=OUTPUT_PATH, debug=DEBUG)
    print("Elapsed time:{}".format(time.time() - start_time))
