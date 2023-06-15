# Dashboard pour la consommation d'énergie des bâtiments à Genève

## Ne fonctionne pas si l'on pas créé au préalable la base de données postgis!

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