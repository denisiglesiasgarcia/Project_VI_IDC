FROM python:3.8-slim-buster
 RUN apt-get update
 RUN apt-get install nano

 RUN mkdir wd
 WORKDIR wd
 COPY app/requirements.txt .
 RUN apt-get update
 RUN apt-get install -y libgdal-dev
 RUN apt-get update &&\
    apt-get install -y binutils libproj-dev gdal-bin
 RUN pip3 install -r requirements.txt

 COPY app/ ./
 COPY data/ ./
 #CMD ['ogr2ogr',' -f "PostgreSQL" PG:"host=127.0.0.1 dbname=gis user=postgres password=docker" "indice3ans_epsg_4326.geojson"']
 CMD [ "python", "test_dash1.py"]
 #CMD ["sleep", "infinity"]
