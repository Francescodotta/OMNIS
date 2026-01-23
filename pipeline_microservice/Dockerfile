FROM python:3.12-slim

WORKDIR /pipeline_microservice

# Installa le dipendenze di sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    git \
    libglib2.0-0 \
    libstdc++6 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libcairo2 \
    openms \
    && rm -rf /var/lib/apt/lists/*

# Copia e installa i requirements
COPY requirements.txt .
RUN git config --global http.proxy "" \
 && git config --global https.proxy ""
RUN pip install --no-cache-dir -r requirements.txt

# Dockerfile

# Crea directory per i logs PRIMA di copiare il codice
RUN mkdir -p logs && chmod -R 777 logs

# Copia il codice dell'applicazione
COPY . .

# Assicurati che i permessi siano corretti
RUN chmod -R 777 logs

EXPOSE 5002

# Il comando verrà sovrascritto da docker-compose
CMD ["python", "run.py"]