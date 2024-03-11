import os
from dotenv import load_dotenv


load_dotenv()

token = os.environ['TOKEN']
global_admins = list(map(int, os.getenv('ADMIN').split(',')))

# const
JSON_FILE_NAME = './bot/data.json'
