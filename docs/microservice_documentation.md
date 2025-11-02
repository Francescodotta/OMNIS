# 4. Microservices Documentation

## Flow Cytometry Microservice

### Purpose
The Flow Cytometry Microservice is responsible for managing the upload, storage, and analysis of flow cytometry data. It provides tools for gating, visualization, and statistical analysis of flow cytometry datasets.

### Architecture
- **Internal Components**:
  - **Gating Module**: Handles gating strategies and gating elements.
  - **Pipeline Processor**: Executes analysis pipelines.
  - **Data Storage**: MongoDB for storing flow cytometry data and metadata.
- **Libraries**:
  - Flask: Web framework.
  - Celery: Task queue for pipeline execution.
  - MongoDB: Database for data storage.
  - FlowKit: Library for flow cytometry data processing.

### Endpoints
#### Example: Upload Flow Cytometry File
- **Endpoint**: `POST /api/v1/project/<project_id>/flow_cytometry`
- **Request**:
  ```json
  {
    "file": "example.fcs",
    "description": "Flow cytometry experiment description"
  }
  ```
- **Response**:
  ```json
  {
    "message": "File uploaded successfully",
    "file_id": "12345"
  }
  ```

#### Example: Retrieve Gating Strategies
- **Endpoint**: `GET /api/v1/project/<project_id>/flow_cytometry/<progressive_id>/gating_strategies`
- **Response**:
  ```json
  [
    {
      "id": "1",
      "name": "Gating Strategy 1",
      "description": "Description of gating strategy"
    }
  ]
  ```

### Data Input/Output Specifications
- **Input**: FCS files for flow cytometry data.
- **Output**: JSON for gating strategies, analysis results, and visualizations.
- **Preprocessing**: Files are validated for format compliance before processing.

### Error Handling
- **Common Error Codes**:
  - `400`: Bad Request (e.g., invalid file format).
  - `404`: Not Found (e.g., file or gating strategy not found).
  - `500`: Internal Server Error.
- **Example Error Response**:
  ```json
  {
    "error": "File format not supported"
  }
  ```

### Configuration & Environment Variables
- `FLOW_CYTOMETRY_ENV`: Environment (e.g., development, production).
- `MONGO_URI_FLOW_CYTOMETRY`: MongoDB connection string.
- `FLOW_CYTOMETRY_FLASK_RUN_PORT`: Port for the Flask application.

### Dockerization
#### Dockerfile Explained
- **Base Image**: Python 3.12 Alpine.
- **Dependencies**: Flask, Celery, MongoDB drivers, FlowKit.
- **Exposed Ports**: `5003` (production), `7003` (development).

#### Build/Run Instructions
1. Build the Docker image:
   ```bash
   docker build -t flow_cytometry_service .
   ```
2. Run the container:
   ```bash
   docker run -p 5003:5003 flow_cytometry_service
   ```

### Testing & Validation
- **Unit Tests**: Test individual endpoints and modules.
- **Integration Tests**: Validate end-to-end workflows.
- **Example Datasets**: Include sample FCS files for testing.

---

## Metabolomics Microservice

### Purpose
The Metabolomics Microservice handles the upload, storage, and analysis of metabolomics data. It supports data preprocessing, peak detection, and pathway analysis.

### Architecture
- **Internal Components**:
  - **Data Processor**: Handles preprocessing and peak detection.
  - **Pipeline Processor**: Executes analysis pipelines.
  - **Data Storage**: MongoDB for storing metabolomics data and metadata.
- **Libraries**:
  - Flask: Web framework.
  - Celery: Task queue for pipeline execution.
  - MongoDB: Database for data storage.
  - OpenMS: Library for metabolomics data processing.

### Endpoints
#### Example: Upload Metabolomics Dataset
- **Endpoint**: `POST /api/project/<project_id>/metabolomics`
- **Request**:
  ```json
  {
    "file": "example.mzML",
    "description": "Metabolomics experiment description"
  }
  ```
- **Response**:
  ```json
  {
    "message": "Dataset uploaded successfully",
    "dataset_id": "67890"
  }
  ```

#### Example: Retrieve Pipelines
- **Endpoint**: `GET /api/v1/project/<project_id>/pipelines`
- **Response**:
  ```json
  [
    {
      "id": "1",
      "name": "Pipeline 1",
      "description": "Description of pipeline"
    }
  ]
  ```

### Data Input/Output Specifications
- **Input**: mzML files for metabolomics data.
- **Output**: JSON for analysis results and visualizations.
- **Preprocessing**: Files are validated for format compliance before processing.

### Error Handling
- **Common Error Codes**:
  - `400`: Bad Request (e.g., invalid file format).
  - `404`: Not Found (e.g., dataset or pipeline not found).
  - `500`: Internal Server Error.
- **Example Error Response**:
  ```json
  {
    "error": "Dataset not found"
  }
  ```

### Configuration & Environment Variables
- `METABOLOMICS_ENV`: Environment (e.g., development, production).
- `MONGO_URI_METABOLOMICS`: MongoDB connection string.
- `METABOLOMICS_FLASK_RUN_PORT`: Port for the Flask application.

### Dockerization
#### Dockerfile Explained
- **Base Image**: Python 3.12 Alpine.
- **Dependencies**: Flask, Celery, MongoDB drivers, OpenMS.
- **Exposed Ports**: `5001` (production), `7001` (development).

#### Build/Run Instructions
1. Build the Docker image:
   ```bash
   docker build -t metabolomics_service .
   ```
2. Run the container:
   ```bash
   docker run -p 5001:5001 metabolomics_service
   ```

### Testing & Validation
- **Unit Tests**: Test individual endpoints and modules.
- **Integration Tests**: Validate end-to-end workflows.
- **Example Datasets**: Include sample mzML files for testing.

---

## Pipeline Microservice

### Purpose
The Pipeline Microservice manages and executes data analysis workflows for multi-omics data. It provides predefined workflows for data normalization, feature extraction, and statistical analysis.

### Architecture
- **Internal Components**:
  - **Workflow Manager**: Handles workflow definitions and execution.
  - **Task Queue**: Celery for asynchronous task execution.
  - **Data Storage**: MongoDB for storing workflow results.
- **Libraries**:
  - Flask: Web framework.
  - Celery: Task queue for workflow execution.
  - MongoDB: Database for data storage.

### Endpoints
#### Example: Execute Workflow
- **Endpoint**: `POST /api/v1/project/<project_id>/process_pipeline`
- **Request**:
  ```json
  {
    "workflow": {
      "steps": [
        {"task": "normalize", "parameters": {"method": "z-score"}},
        {"task": "feature_extraction", "parameters": {"threshold": 0.05}}
      ]
    }
  }
  ```
- **Response**:
  ```json
  {
    "message": "Workflow executed successfully",
    "results": "results.json"
  }
  ```

### Data Input/Output Specifications
- **Input**: JSON workflow definitions.
- **Output**: JSON results and logs.
- **Preprocessing**: Validates workflow definitions before execution.

### Error Handling
- **Common Error Codes**:
  - `400`: Bad Request (e.g., invalid workflow definition).
  - `404`: Not Found (e.g., workflow not found).
  - `500`: Internal Server Error.
- **Example Error Response**:
  ```json
  {
    "error": "Invalid workflow definition"
  }
  ```

### Configuration & Environment Variables
- `PIPELINE_ENV`: Environment (e.g., development, production).
- `MONGO_URI_PIPELINE`: MongoDB connection string.
- `PIPELINE_FLASK_RUN_PORT`: Port for the Flask application.

### Dockerization
#### Dockerfile Explained
- **Base Image**: Python 3.12 Alpine.
- **Dependencies**: Flask, Celery, MongoDB drivers.
- **Exposed Ports**: `5002` (production), `7002` (development).

#### Build/Run Instructions
1. Build the Docker image:
   ```bash
   docker build -t pipeline_service .
   ```
2. Run the container:
   ```bash
   docker run -p 5002:5002 pipeline_service
   ```

### Testing & Validation
- **Unit Tests**: Test individual endpoints and modules.
- **Integration Tests**: Validate end-to-end workflows.
- **Example Workflows**: Include sample JSON workflows for testing.