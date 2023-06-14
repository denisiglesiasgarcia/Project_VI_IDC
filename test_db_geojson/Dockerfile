# Dockerfile
FROM postgis/postgis:15-3.3

# Set environment variables
ENV POSTGRES_PASSWORD=postgis
ENV POSTGRES_USER=postgis
ENV POSTGRES_DB=mydatabase

# Updating packages and installing necessary dependencies
RUN apt-get update && \
    apt-get install -y nano libgdal-dev binutils libproj-dev gdal-bin python3 postgresql-client python3-pip && \
    apt-get clean 

# Copying app and data into the container
COPY app/ /app/
COPY data/ /data/
COPY import_data.sh /docker-entrypoint-initdb.d/import_data.sh

RUN pip3 install -r /app/requirements.txt

# Create an initialization script
# RUN echo '#!/bin/bash\n\
#           set -e\n\
#           psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL\n\
#           CREATE DATABASE $POSTGRES_DB;\n\
#           \\c $POSTGRES_DB\n\
#           CREATE EXTENSION postgis;\n\
#           EOSQL\n'\
#           > /docker-entrypoint-initdb.d/initdb.sh && chmod +x /docker-entrypoint-initdb.d/initdb.sh

# Start the Dash app
#CMD ["python3", "/app/app.py"]
