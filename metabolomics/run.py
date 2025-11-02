from app import app
from dotenv import load_dotenv
import os

load_dotenv()

metabo_port = os.getenv("FLASK_RUN_METABOLOMICS_PORT")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001, debug=False)
