import os
from dotenv import load_dotenv


load_dotenv()

token = os.environ['TOKEN']
admin = int(os.getenv('ADMIN'))
