from app import app
import os 
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
# Set the environment variable for the Flask app
os.environ['FLASK_ENV'] = os.getenv('FLASK_ENV', 'development')

if __name__ == "__main__":
    # Run the Flask app
    # Use the port from environment variable or default to 5000
    # Debug mode is enabled if FLASK_ENV is 'development'
    debug = os.getenv('AUTH_ENV') == 'development'
    if debug:
        print("Running in development mode")
        port = os.getenv('FLASK_RUN_AUTH_DEV_PORT', 7000)
        app.run(host= '0.0.0.0', port=port, debug=True)
    else:
        port = os.getenv('FLASK_RUN_AUTH_PROD_PORT', 5000)
        print("Running in production mode")
        app.run(host='0.0.0.0', port=port, debug=True)
