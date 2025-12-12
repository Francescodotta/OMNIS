# Usa un'immagine base di Python
FROM python:3.12-alpine3.20

# Set working directory
WORKDIR /auth_microservice

# Install system dependencies 
RUN apk add --no-cache gcc musl-dev


# Copy the requirements.txt file and install Python dependencies
# Copy the requirements.txt file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# Copy the application code 
COPY . .

# Create the logs directory within the application folder
RUN mkdir -p logs

# Set environment variables
# These will be overridden by docker-compose
ENV FLASK_ENV=production
ENV MONGO_URI_AUTH=unknown
ENV FLASK_AUTH_PORT=5000

# Expose the port that the application runs on
# This will be dynamically set based on the environment
EXPOSE 5000 

# Command to start the application using the run.py script
CMD ["sh", "-c", "python create_admin.py && python run.py"]