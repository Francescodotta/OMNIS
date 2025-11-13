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
    && rm -rf /var/lib/apt/lists/*

# Copia e installa i requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# install openms via URL (passare OPENMS_DEB_URL in build)
ARG OPENMS_DEB_URL
RUN set -eux; \
    if [ -n "$OPENMS_DEB_URL" ]; then \
      apt-get update; apt-get install -y --no-install-recommends wget ca-certificates && \
      wget -O /tmp/OpenMS.deb "$OPENMS_DEB_URL" && \
      dpkg -i /tmp/OpenMS.deb || true && apt-get -f install -y && \
      rm -f /tmp/OpenMS.deb && apt-get purge -y --auto-remove wget && \
      rm -rf /var/lib/apt/lists/*; \
    fi

# Copia il codice dell'applicazione
COPY . .

# Crea directory per i logs
RUN mkdir -p logs

EXPOSE 5002

# Il comando verrà sovrascritto da docker-compose
CMD ["python", "run.py"]