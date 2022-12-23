sleep 15
ogr2ogr -f "PostgreSQL" PG:"host=127.0.0.1 dbname=postgres user=postgres password=docker" "test/indice3ans_epsg_4326.geojson"