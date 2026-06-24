import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
bot_token = os.getenv('BOT_TOKEN')
db_user = os.getenv('DB_USER')
db_host = os.getenv('DB_HOST')
db_passwd = os.getenv('DB_PASSWD')