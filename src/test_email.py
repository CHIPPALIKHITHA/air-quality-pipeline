from dotenv import load_dotenv

from alerts import send_email

load_dotenv()
send_email("Air quality pipeline test", "If you can read this, email alerts work.")
print("Email sent")