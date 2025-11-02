FROM python:3.12-alpine3.20

WORKDIR /flow_cytometry_microservice

# Install system dependencies
# Install system dependencies
# Install system dependencies
RUN apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    python3-dev \
    libffi-dev \
    libc-dev \
    libstdc++ \
    libx11 \
    libxrender \
    libxext \
    fontconfig 


# Copy the requirements.txt file and install Python dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create the logs directory within the application folder
RUN mkdir -p logs

# Set environment variables
# These will be overridden by docker-compose
ENV FLOW_CYTOMETRY_ENV=production
ENV MONGO_URI_FLOW_CYTOMETRY=unknown
ENV FLOW_CYTOMETRY_FLASK_RUN_DEVELOPMENT_PORT=7003
ENV FLOW_CYTOMETRY_FLASK_RUN_PRODUCTION_PORT=5003

# Expose the port that the application runs on
# This will be dynamically set based on the environment
EXPOSE 5003 7003

# Command to start the application using the run.py script
CMD ["python", "run.py"]