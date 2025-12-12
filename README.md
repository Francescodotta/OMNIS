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


2. **Environment Configuration**:
- Create a `.env` file in the root directory with necessary variables (e.g., `MONGO_URI`, API keys, ports).
- Example:
  ```
  MONGO_URI=mongodb://localhost:27017/omnis
  FLASK_ENV=development
  REACT_APP_API_BASE_URL=http://localhost:5000
  ```

3. **Build and Run with Docker Compose**:
- Ensure Docker is running.
- Run: `docker-compose up --build`
- This will start MongoDB, all microservices, and the frontend.

4. **Individual Service Setup** (if not using Docker):
- **Frontend**: `cd frontend && npm install && npm start`
- **Microservices**: For each (e.g., metabolomics), `cd <service-dir> && pip install -r requirements.txt && python run.py`
- Install MongoDB separately if needed.

5. **Database Initialization**:
- MongoDB will be initialized via Docker. Ensure collections for users, projects, and data are set up as per the models.

## Usage
- **Access the Application**: Open `http://localhost:3000` (React frontend) in your browser.
- **User Registration/Login**: Use the auth microservice for account management.
- **Data Upload**: Upload files via the frontend, specifying project and metadata.
- **Pipeline Execution**: Configure and run analysis pipelines through the pipeline microservice.
- **Results Retrieval**: View and download processed data and visualizations.
- **API Endpoints**: Refer to individual microservice docs (e.g., `/api/v1/project/{id}/flow_cytometry/upload` for cytometry).

For detailed API documentation, see the Swagger/OpenAPI specs in each microservice.

## Development
- **Code Structure**: Each microservice has its own directory with `app/`, `models/`, `views/`, etc.
- **Testing**: Run unit tests with `pytest` in each service.
- **Contributing**: Fork the repo, create a feature branch, and submit a PR. Follow PEP8 for Python and ESLint for React.

## Troubleshooting
- **Common Issues**: Check Docker logs (`docker-compose logs`). Ensure ports (e.g., 5001 for prod) are not in use.
- **File Upload Errors**: Verify filename sanitization (e.g., handle special chars like `#`).
- **Pipeline Failures**: Check pipeline microservice logs for computation errors.

## License
This project is licensed under [MIT License](LICENSE). See the LICENSE file for details.

## Contact
For questions or support, contact the development team at [email@example.com] or open an issue on GitHub.