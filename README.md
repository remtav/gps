# À propos*

Le script *bilanroutier.py* permet de localiser l'emplacement approximatif d'un accident répertorié dans le bilan routier du Québec (fichier csv).

\* Le script en est à sa première version fonctionnelle. Plusieurs améliorations pourront être apportées par l'utilisateur selon ses besoins (et sa connaissance de Python!). 

# Installation

Le script nécessite Python 3. Nous recommandons l'utilisation d'[environnements conda](https://conda.io/projects/conda/en/latest/user-guide/install/index.html). La commande classique *pip install* peut aussi être utilisée.
Les 4 modules suivants doivent être installés*:
- Pandas
- Geopandas
- Numpy
- Geopy

\* Un environnement conda valide (mais contenant plusieurs modules inutiles) peut également être créé de toutes pièces en utilisant le fichier environement.yml contenu dans ce projet. N.B. Cette approche n'a pas été testée. 

# Description

## Input

En entrée, le script prend comme argument le chemin vers le fichier .csv de bilan routier ou vers le répertoire contenant ce(s) fichier(s) si l'utilisateur souhaite parcourir des .csv de plusieurs années consécutives, par exemple.

> Si un répertoire est fourni, le script lira en boucle tous les fichiers .csv contenus dans ce répertoire.

Exemple d'exécution:

`python bilanroutier.py path/to/directory/rapports-accident-2019.csv` 

ou 

`python bilanroutier.py path/to/directory-with-csv`

## Output

Le script *bilanroutier.py* écrit un fichier *rapports_accident.gpkg* (pour plus d'info sur le format geopackage, voir https://fr.wikipedia.org/wiki/Geopackage. Par défaut, ce fichier est écrit dans le même répertoire que celui-ci où se trouve le script. Ce fichier peut être ouvert par un logiciel SIG tel que [QGIS](https://www.qgis.org/en/site/forusers/download.html).

## Détails de l'exécution

Lors de l'exécution du script *bilanroutier.py*, celui-ci lit d'abord le .csv. Dans la version actuelle, les données sont filtrées pour conserver uniquement les accidents à Sherbrooke et impliquant au moins un piéton comme victime*. Puis, le script itère dans le tableau résultat, ligne par ligne. À chaque ligne, voici ce qui est effectué:
- Identifie l'adresse ou l'intersection de l'accident (certaines erreurs peuvent survenir, car les données ne sont pas toujours entrées de manière uniforme)
- Prépare la chaîne de caractères qui sera soumise au service de geocodage (Google, le cas échéant)
- Soumet la requête au service de géocodage de Google

Puis, le fichier *rapports_accident.gpkg* est généré à partir de toutes les lignes pour lesquelles Google a renvoyé des coordonnées de latitude/longitude.
