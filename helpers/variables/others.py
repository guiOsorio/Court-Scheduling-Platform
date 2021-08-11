import os

# Dotenv
from dotenv import load_dotenv
load_dotenv()

# Get environment variables
# Secret password to create a new admin
ADMIN_SECRET_PASSWORD = os.environ.get('ADMIN_SECRET_PASSWORD')
# Link to connect to ElephantSQL database
POSTGRE_URI = os.environ.get('POSTGRE_URI')

# Store program's name
appname = "Scheduling"
# Store program's name
appname = "Scheduling"
path_to_site = "#"

# Store links to show at the end of emails
link_to_site = f'<p>Visit us at <a href="{path_to_site}">{appname}.com</a></p>'     ############ HERE (update link to show correct website)




# CHANGE PASSWORD BY EMAIL