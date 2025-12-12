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
    port = os.getenv('FLASK_AUTH_PORT', 500)
    app.run(host= '0.0.0.0', port=port, debug=True)

