# OMNIS
Computational framework for quantitative multi-omics analysis

## Overview
OMNIS is a comprehensive platform for multi-omics data analysis, enabling researchers to upload, process, and analyze data from various omics domains such as flow cytometry and metabolomics. It supports secure file handling, pipeline execution, and visualization of results, all within a scalable microservices architecture.

## Architecture
OMNIS follows a microservices-based architecture to ensure modularity, scalability, and ease of maintenance. The system is composed of the following components:

- **Frontend**: Built with React, providing a user-friendly web interface for data uploads, pipeline configuration, result visualization, and user management.
- **Microservices**:
  - **Auth Microservice**: Handles user authentication, authorization, and session management using Flask.
  - **Metabolomics Microservice**: Manages metabolomics data processing, including file uploads (e.g., raw files parsed with ThermoRawFileParser), analysis, and result retrieval. Built with Flask and containerized with Docker.
  - **Flow Cytometry Microservice**: Handles flow cytometry data (e.g., FCS files), including batch uploads, metadata management, pipeline runs (e.g., gating, clustering), and visualizations (e.g., UMAP, heatmaps). Built with Flask, integrates with libraries like FlowKit.
  - **Pipeline Microservice**: Dedicated to computational analysis workflows, executing pipelines for data processing across omics types. It coordinates heavy computations and integrates with external tools.
- **Database**: MongoDB, running in a Docker container for data persistence. Handles encrypted storage of files, metadata, user data, and pipeline results.
- **Infrastructure**: All services are containerized with Docker for easy deployment. Communication between services uses RESTful APIs. Data security is enforced through encryption (e.g., for file storage) and user permission checks.

The architecture supports horizontal scaling, with services communicating asynchronously where needed.

## Features
- **Multi-Omics Support**: Integrated workflows for flow cytometry and metabolomics data.
- **Secure Data Handling**: File encryption, secure uploads, and user-based access control.
- **Pipeline Execution**: Configurable analysis pipelines with support for batch processing and result export.
- **Visualization**: Interactive results (e.g., heatmaps, UMAP plots) via the React frontend.
- **Batch Operations**: Upload and manage multiple files at once.
- **Logging and Monitoring**: Custom logging for errors and activities.
- **Dockerized Deployment**: Easy setup and scaling with Docker Compose.

## Prerequisites
- Docker and Docker Compose
- Node.js (for frontend development)
- Python 3.12 (for microservices)
- MongoDB (handled via Docker, but ensure ports are available)

## Installation and Setup
1. **Clone the Repository**:
    ```bash
    git clone git@github.com:Francescodotta/OMNIS.git
    cd OMNIS
    ```


2. **Start MongoDB container**:
  ```bash
    cd mongodb_docker
    docker-compose up -d --build
  ```
3. **Populate the .env of auth_microservice**:
   - Copy the provided `env_example.txt` to `.env` and fill in the required environment variables, including `MONGO_URI_AUTH` pointing to the MongoDB instance.

   - You need also to create the following secret keys for encryption and JWT:
     - `FERNET_SECRET_KEY`
     - `METABOLOMICS_SECRET_KEY`
     - `FLOW_CYTOMETRY_SECRET_KEY`
     - `JWT_SECRET_KEY`

     The code to generate the Fernet key and the JWT secret key can be found in the `auth_microservice` folder within the app/private directory. (***crypto.py***,***jwt.py***)

     For each microservice, you'll find the .env example file in their respective directories.

4. **Start Microservices**:
    - Navigate to each microservice directory (e.g., `auth_microservice`, `metabolomics_microservice`, `flow_cytometry_microservice`, `pipeline_microservice`) and run:
    ```bash
    docker-compose up -d --build
    ```

5. **Start Frontend**:
    ```bash
    cd omnis_frontend
    docker-compose up -d --build
    ```

In the auth_microservice there is the **create_admin.py** script that allows you to create the first admin user to access the platform. Run it after starting the auth_microservice container.

## License
This project is licensed under [MIT License](LICENSE). See the LICENSE file for details.

## Contact
For questions or support, contact the development team at [email@example.com] or open an issue on GitHub.