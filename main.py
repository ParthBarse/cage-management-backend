from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Access the environment variables
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')

# Use the environment variables in your application
print(f'Database Host: {db_host}')
print(f'Database User: {db_user}')
print(f'Database Password: {db_pass}')
