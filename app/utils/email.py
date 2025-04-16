import random
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from config import SENDER_MAIL, SENDER_PASSWORD


def generate_verification_code():
    return str(random.randint(100000, 999999))


def send_verification(recipient_email, verification_code):
    subject = "Подтверждение почты в сапёре"
    text = f"Ваш код подтверждения: {verification_code}"

    msg = MIMEText(text, 'plain', 'utf-8')
    msg['Subject'] = Header(subject, 'utf-8')

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(SENDER_MAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_MAIL, recipient_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False 