FROM mongo:7.0

# Copia script di inizializzazione (opzionale, per creare DB/utenti)
COPY init-mongo.js /docker-entrypoint-initdb.d/

# Espone la porta MongoDB
EXPOSE 27017