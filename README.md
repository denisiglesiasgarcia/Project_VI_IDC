# Dashboard pour la consommation d'énergie des bâtiments à Genève

## Ne fonctionne pas si l'on pas créé au préalable la base de données postgis!

## TODO
- Améliorer la performance au lancement, ça prends bien 5 minutes mais après c'est super fluide → profiler?
- Ajouter autres informations pertinentes
- Compléter le readme avec la partie de comment faire la base de données avec les données géographiques

## Installation

### conda
```shell
conda env create --name dashidc --file=environment.yml
```
### pip
```shell
pip install -r requirements.txt
```

## Lancement
```shell
conda activate dashidc
```
```shell
python app.py
```
