from app.models.metabolomics_models import MetabolomicsModel, AuthModel, ProjectModel, MemberModel
import os
from dotenv import load_dotenv  
from cryptography.fernet import Fernet

load_dotenv()
METABOLOMICS_SAVE_PATH = os.getenv("METABOLOMICS_SAVE_PATH")

METABOLOMICS_SECRET_KEY = os.getenv('METABOLOMICS_SECRET_KEY')  

# funzione per validare i dati in input da un esperimento di metabolomica
def validate_metabolomics_data(username, project_id, experimentName, files):
    # l'utente deve essere registrato
    user = AuthModel.find_user_by_username(username)
    if not user:
        return {"error": "User not found"}, 404
    # il progetto deve essere presente nel database
    project = ProjectModel.find_by_id(int(project_id))
    if not project:
        return {"error": "Project not found"}, 404

    # controlla che il nome dell'esperimento non sia già presente nel database
    experiment = MetabolomicsModel.find_by_name(experimentName)
    if experiment:
        print("experiment already exists")
        return {"error": "Experiment name already exists"}, 400
    # controllo che il file non sia già presente
    if os.path.exists(METABOLOMICS_SAVE_PATH + files.filename):
        return {"error": "File already exists"}, 400
    return {"message": "Data validated"}, 200


def save_file(file):
    try:
        file.save(METABOLOMICS_SAVE_PATH + file.filename)
    # se c'è qualche errore
    except Exception as e:
        return {"error": str(e)}, 500
    return METABOLOMICS_SAVE_PATH + file.filename,200


def validate_pipeline_data(user_id, project_id):
    # l'utente deve essere registrato
    user = AuthModel.find_user_by_username(user_id)
    if not user:
        return {"error": "User not found"}, 404
    # il progetto deve essere presente nel database
    project = ProjectModel.find_by_id(int(project_id))
    if not project:
        return {"error": "Project not found"}, 404
    return {"message": "Data validated"}, 200


# valida utente come membro del progetto
def validate_user_project(username, project_id):
    # prendi user progressive id da username
    user_id = AuthModel.find_user_by_username(username)["progressive_id"]
    # controlla che l'utente sia membro del progetto
    member = MemberModel.find_by_project_id(int(project_id), user_id)
    if not member:
        return {"error": "User is not a member of the project"}, 400
    return {"message": "User validated"}, 200

# valida l'utente come admin del progetto
def is_user_admin(username, project_id):
    # prendi user progressive id da username
    user_id = AuthModel.find_user_by_username(username)["progressive_id"]
    # controlla che l'utente sia admin del progetto
    member = MemberModel.find_by_project_id(int(project_id), user_id)
    if not member:
        return {"error": "User is not a member of the project"}, 400
    if member["role"] != "PI":
        return {"error": "User is not an admin of the project"}, 400
    return {"message": "User is an admin"}, 200

