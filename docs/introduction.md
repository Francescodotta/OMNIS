# OMNIS INTRODUCTION
OMNIS is a computational framework designed to facilitate the data storage, analysis and sharing of multi-omics data. It provides a user-friendly interface available through a web browser, allowing researchers to easily manage and explore their datasets. At this moment it comes with two microservices designed to handle metabolomics and flow cytometry data, with plans to expand to other omics types in the future. Another microservice, called Auth, is designed to handle user authentication and authorization, ensuring secure access to the platform. The data analysis steps are supported by a microservice called Pipeline, which provides a set of predefined workflows for processing and analyzing multi-omics data. The platform is built using modern web technologies and is designed to be scalable and extensible, allowing for easy integration of new features and functionalities. The workflows sent from the front-end to the pipeline microservice are executed using Celery, a distributed task queue that allows for parallel processing of tasks across multiple workers. This ensures that the platform can handle large datasets and complex analyses efficiently. The backend of OMNIS is built using Flask, a lightweight web framework for Python, which provides a simple and flexible way to build web applications. The frontend is built using React.js, a popular JavaScript library for building user interfaces, which allows for a responsive and interactive user experience. The platform is containerized using Docker, which makes it easy to deploy and manage the different microservices. Overall, OMNIS is a powerful and flexible platform for multi-omics data analysis that is designed to meet the needs of modern biological research.



## Key Features
- **Multi-Omics Support**: OMNIS supports various types of omics data, including metabolomics and flow cytometry, with plans to expand to other omics types in the future.
- **User-Friendly Interface**: The platform provides an intuitive web-based interface for easy data management and exploration.
- **Secure Authentication**: The Auth microservice ensures secure access to the platform through user authentication and authorization. It also provides permission-based access control to ensure that users can only access data and functionalities they are authorized to use.
- **No-Code Workflows**: The Pipeline microservice offers predefined workflows for data processing and analysis, allowing users to perform complex analyses without writing code. This technology is served using React-Flow, a library for building node-based editors in React.
- **Scalability**: The platform is designed to be scalable, allowing for easy integration of new features and functionalities.
- **Efficient Task Processing**: The use of Celery for task execution ensures efficient handling of large datasets and complex analyses through parallel processing.
- **Containerization**: The use of Docker for containerization simplifies deployment and management of the different microservices.
- **Extensibility**: The modular architecture of OMNIS allows for easy addition of new microservices and functionalities as needed.


## Technology Stack
- **Backend**: Flask, Celery, Redis, MongoDB
- **Frontend**: React.js, JavaScript
- **Containerization**: Docker, Docker Compose


## Getting Started
To get started with OMNIS, follow these steps:
1. Clone the OMNIS repository from GitHub.
2. Install Docker and Docker Compose on your machine.
3. Navigate to the root directory of the OMNIS repository.
4. Run the following command to build and start the OMNIS services:
   ```bash
   docker-compose up --build
   ```
5. Open your web browser and navigate to `http://localhost:3000` to access the OMNIS web interface.
6. Create an account and log in to start using the platform.    


## SYSTEM ARCHITECTURE
OMNIS is built using a microservices architecture, with each microservice responsible for a specific functionality. The main components of the system include:
- **Auth Microservice**: Handles user authentication and authorization, ensuring secure access to the platform.
- **Pipeline Microservice**: Provides predefined workflows for data processing and analysis, allowing users to perform complex analyses without writing code.
- **Database**: MongoDB is used to store user data, omics data, and analysis results.
- **Task Queue**: Celery is used to manage and execute tasks asynchronously, allowing for efficient handling of large datasets and complex analyses.
- **Frontend**: Built using React.js, the frontend provides a user-friendly interface for data management and exploration.  


Each -omics technology has its own microservice that handles data upload, storage, and specific analysis workflows. The microservices communicate with each other through RESTful APIs, allowing for seamless integration and data exchange between different components of the system. In addition, each omics microservice can be independently stored within a unique MongoDB database, ensuring data isolation and security. This modular approach allows for easy addition of new omics types in the future, as each new microservice can be developed and integrated without affecting the existing components of the system. The data can be uploaded through the web interface, where users can select the appropriate microservice for their omics data type. Once uploaded, the data is stored in the corresponding MongoDB database and can be accessed and analyzed using the predefined workflows provided by the Pipeline microservice. The use of Docker for containerization ensures that each microservice can be deployed and managed independently, allowing for easy scaling and maintenance of the system. Overall, the microservices architecture of OMNIS provides a flexible and extensible platform for multi-omics data analysis that can adapt to the evolving needs of biological research.
**Auth Microservice**:
The auth microservice is responsible for managing user authentication and authorization within the OMNIS platform. It provides a secure way for users to create accounts, log in, and access the various features and functionalities of the system. The auth microservice uses JWT (JSON Web Tokens) for authentication, which allows for stateless and secure communication between the client and server. When a user logs in, the auth microservice generates a JWT token that contains information about the user's identity and permissions. This token is then sent to the client, which includes it in subsequent requests to access protected resources. The auth microservice verifies the token on each request to ensure that the user is authorized to access the requested resource. In addition to authentication, the auth microservice also provides permission-based access control, allowing administrators to define different roles and permissions for users. This ensures that users can only access data and functionalities they are authorized to use, enhancing the security of the platform. The auth microservice is built using Flask, a lightweight web framework for Python, and uses MongoDB to store user data and permissions. It communicates with other microservices through RESTful APIs, allowing for seamless integration and data exchange between different components of the system. Overall, the auth microservice plays a crucial role in ensuring the security and integrity of the OMNIS platform, providing a robust authentication and authorization mechanism for users. This microservice is also responsible for project management. This platform enables users to create and manage projects, within different biological fields (e.g., metabolomics, flow cytometry). Each project can have multiple users with different roles and permissions, allowing for collaborative work on data analysis and interpretation. Users can create new projects, invite collaborators, and assign specific roles (e.g., admin, editor, viewer) to each user. This ensures that project members have appropriate access to data and functionalities based on their roles. The auth microservice handles all aspects of project management, including creating, updating, and deleting projects, as well as managing user roles and permissions within each project. It provides a secure and organized way for researchers to collaborate on multi-omics data analysis within the OMNIS platform.
**Pipeline Microservice**:
The pipeline microservice is a core component of the OMNIS platform, responsible for managing and executing data analysis workflows for multi-omics data. It provides a set of predefined workflows that users can utilize to process and analyze their datasets without the need for coding. The pipeline microservice is designed to be flexible and extensible, allowing for the addition of new workflows and functionalities as needed. Users can select from a variety of analysis workflows tailored to different omics data types, such as metabolomics and flow cytometry. The workflows are designed in the frontend by the user which specifies nodes and connections, these are then translated into a JSON object which is passed to the pipeline microservice which, through a celery task, executes the workflow step by step. Each step in the workflow corresponds to a specific data processing or analysis task, such as data normalization, feature extraction, statistical analysis, or visualization. The pipeline microservice uses Celery, a distributed task queue, to manage and execute these tasks asynchronously. This allows for efficient handling of large datasets and complex analyses by distributing the workload across multiple workers. The results of each analysis step are stored in the MongoDB database, allowing users to access and explore their results through the OMNIS web interface. The pipeline microservice communicates with other microservices through RESTful APIs, enabling seamless integration and data exchange between different components of the system. Overall, the pipeline microservice provides a powerful and user-friendly way for researchers to perform multi-omics data analysis within the OMNIS platform, streamlining the data processing workflow and facilitating biological discovery.
**Flow Cytometry Microservice**:
The flow cytometry microservice is a specialized component of the OMNIS platform designed to handle the upload, storage, and analysis of flow cytometry data. Flow cytometry is a powerful technique used to analyze the physical and chemical characteristics of cells or particles in a fluid as they pass through a laser beam. The flow cytometry microservice provides a user-friendly interface for researchers to manage their flow cytometry datasets and perform various analyses. Users can upload their flow cytometry data files (e.g., FCS files) through the OMNIS web interface, where the microservice processes and stores the data in a dedicated MongoDB database. At the moment the microservice can handle the gating directly into the platform, allowing users to define and apply gates to their data for cell population identification and analysis. Gating is performed directly in the frontend of the application using a graphical interface built with 3Djs. They can draw connected points within the scatterplot to define the polygonal gate, which is then applied to the data to select the specific cell populations of interest. The gate is then saved into a json format for future reference and analysis, it also is saved into a gml file which is compliance to the GatingML 2.0 standard designed from the ISAC (International Society for Advancement of Cytometry). The microservice also provides various analysis tools, such as data visualization, statistical analysis, and machine learning algorithms, to help users interpret their flow cytometry data. Using the graphical interface, users can create and customize pipelines, through a drag-and-drop interface created using the React-Flow library, to perform complex analyses on their datasets. The flow cytometry microservice communicates with other microservices through RESTful APIs, allowing for seamless integration and data exchange between different components of the OMNIS platform. Overall, the flow cytometry microservice provides a comprehensive solution for managing and analyzing flow cytometry data within the OMNIS platform, enabling researchers to gain valuable insights into their biological samples.
**Metabolomics Microservice**:
The metabolomics microservice is a dedicated component of the OMNIS platform designed to handle the upload, storage, and analysis of metabolomics data. Metabolomics is the comprehensive study of small molecules, known as metabolites, within cells, biofluids, tissues, or organisms. The metabolomics microservice provides a user-friendly interface for researchers to manage their metabolomics datasets and perform various analyses. Users can upload their metabolomics data files (e.g., mass spectrometry data) through the OMNIS web interface, where the microservice processes and stores the data in a dedicated MongoDB database. The microservice supports various data formats commonly used in metabolomics, ensuring compatibility with a wide range of instruments and software. The metabolomics microservice offers a variety of analysis tools, such as data preprocessing, peak detection, compound identification, statistical analysis, and pathway analysis. Users can create and customize analysis pipelines through a drag-and-drop interface created using the React-Flow library, allowing for complex analyses on their datasets without the need for coding. The microservice leverages powerful computational tools, such as OpenMS, to perform advanced data processing and analysis tasks. The metabolomics microservice communicates with other microservices through RESTful APIs, enabling seamless integration and data exchange between different components of the OMNIS platform. Overall, the metabolomics microservice provides a comprehensive solution for managing and analyzing metabolomics data within the OMNIS platform, empowering researchers to gain valuable insights into the metabolic profiles of their biological samples.


## Communication Between Microservices
The microservices within the OMNIS platform communicate with each other through RESTful APIs (Application Programming Interfaces). RESTful APIs provide a standardized way for different components of the system to exchange data and interact with each other. Each microservice exposes a set of endpoints that can be accessed by other microservices or the frontend application. These endpoints allow for various operations, such as creating, reading, updating, and deleting resources (CRUD operations). For example, the auth microservice provides endpoints for user authentication and authorization, while the pipeline microservice offers endpoints for managing and executing data analysis workflows. When a user interacts with the OMNIS web interface, the frontend application sends requests to the appropriate microservices through their RESTful APIs. The microservices process these requests and return the relevant data or perform the requested actions. This modular approach allows for seamless integration and data exchange between different components of the system, enabling a cohesive and efficient user experience. Additionally, the use of RESTful APIs allows for easy scalability and extensibility of the platform, as new microservices can be added or existing ones can be modified without affecting the overall functionality of the system. Overall, RESTful APIs play a crucial role in facilitating communication between the microservices within the OMNIS platform, ensuring smooth operation and interaction between different components of the system.

## Flow Cytometry Microservice Endpoints

### General Endpoints
- **POST** `/api/v1/project/<project_id>/flow_cytometry`  
  Upload a single flow cytometry file.

- **POST** `/api/v1/project/<project_id>/flow_cytometry/batch`  
  Upload multiple flow cytometry files in batch.

- **GET** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>`  
  Retrieve a specific flow cytometry file by its progressive ID.

- **GET** `/api/v1/project/<project_id>/flow_cytometry`  
  Retrieve all flow cytometry files for a project.

- **PUT** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>`  
  Update metadata for a specific flow cytometry file.

- **DELETE** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>`  
  Delete a specific flow cytometry file.

### Pipeline Endpoints
- **POST** `/api/v1/project/<project_id>/pipeline`  
  Save a pipeline for flow cytometry.

- **POST** `/api/v1/project/<project_id>/process_pipeline`  
  Process a pipeline for flow cytometry.

- **GET** `/api/v1/project/<project_id>/running_pipelines`  
  Retrieve all running pipelines for a project.

- **GET** `/api/v1/project/<project_id>/running_pipeline/<pipeline_id>`  
  Retrieve details of a specific running pipeline.

- **GET** `/api/v1/project/<project_id>/heatmap/<pipeline_id>`  
  Retrieve heatmap data for a specific pipeline.

### Gating Endpoints
- **GET** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>/gating_strategies/<gating_strategy_id>/scatterplot`  
  Retrieve scatterplot data for a gating strategy.

- **GET** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>/gates`  
  Retrieve all gates for a specific flow cytometry file.

- **POST** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>/gating_strategies`  
  Create a new gating strategy.

- **GET** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>/gating_strategies`  
  Retrieve all gating strategies for a specific flow cytometry file.

- **GET** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>/gating_strategies/<gating_strategy_id>`  
  Retrieve a specific gating strategy by its ID.

- **DELETE** `/api/v1/project/<project_id>/flow_cytometry/<progressive_id>/gating_strategies/<gating_strategy_id>`  
  Delete a specific gating strategy.

### Gating Elements Endpoints
- **GET** `/api/v1/project/<project_id>/flow_cytometry/<flow_cytometry_id>/gating_strategies/<gating_strategy_id>/gating_elements`  
  Retrieve all gating elements for a gating strategy.

- **POST** `/api/v1/project/<project_id>/flow_cytometry/<flow_cytometry_id>/gating_strategies/<gating_strategy_id>/gating_elements`  
  Create a new gating element for a gating strategy.

- **DELETE** `/api/v1/project/<project_id>/flow_cytometry/<flow_cytometry_id>/gating_strategies/<gating_strategy_id>/gating_elements/<gating_element_id>`  
  Delete a specific gating element.


## Metabolomics Microservice Endpoints

### General Endpoints
- **POST** `/api/project/<project_id>/metabolomics`  
  Upload a metabolomics dataset for a specific project.

- **POST** `/api/v1/project/<project_id>/metabolomics_experiments`  
  Create a new metabolomics experiment.

- **GET** `/api/metabolomics/<metabolomics_id>`  
  Retrieve details of a specific metabolomics dataset.

- **GET** `/api/project/<project_id>/metabolomics`  
  Retrieve all metabolomics datasets for a project.

### Pipeline Endpoints
- **POST** `/api/project/<project_id>/process_pipeline`  
  Process a metabolomics pipeline for the specified project.

- **POST** `/api/project/<project_id>/pipeline`  
  Save a metabolomics pipeline within the specified project.

- **GET** `/api/v1/project/<project_id>/pipelines`  
  Retrieve all pipelines for the specified project.

- **DELETE** `/api/v1/project/<project_id>/pipelines/<pipeline_id>`  
  Delete a specific pipeline from the project.

- **GET** `/api/v1/project/<project_id>/pipelines/<pipeline_id>/results`  
  Retrieve results of a specific pipeline.

### Chunk Upload Endpoint
- **POST** `/api/v1/project/<project_id>/metabolomics_experiment/upload_chunk`  
  Upload a chunk of data for a metabolomics experiment.

