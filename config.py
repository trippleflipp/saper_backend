from dotenv import load_dotenv
import os

load_dotenv()

DB_USER = os.getenv("user")
DB_PASSWORD = os.getenv("password") 
DB_HOST = os.getenv("host")
DB_PORT = os.getenv("port")
DB_NAME = os.getenv("dbname")

SENDER_MAIL = os.getenv("sender_mail")
SENDER_PASSWORD = str(os.getenv("sender_password"))