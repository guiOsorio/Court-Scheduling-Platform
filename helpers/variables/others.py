import os

# Dotenv
from dotenv import load_dotenv
load_dotenv()

# Link to connect to ElephantSQL database
POSTGRE_URI = os.environ.get('POSTGRE_URI')