FROM python:3.12-slim

WORKDIR /metabolomics_microservice

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libglib2.0-0 \
    libstdc++6 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libfontconfig1 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements.txt file and install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create the logs directory within the application folder
RUN mkdir -p logs

# Set environment variables
# These will be overridden by docker-compose
ENV METABOLOMICS_ENV=production
ENV MONGO_URI_METABOLOMICS=unknown
ENV METABOLOMICS_FLASK_RUN_DEV_PORT=7001
ENV METABOLOMICS_FLASK_RUN_PROD_PORT=5001
# Expose the port that the application runs on
# This will be dynamically set based on the environment
EXPOSE 5001 7001

# Command to start the application using the run.py script
CMD ["python", "run.py"]