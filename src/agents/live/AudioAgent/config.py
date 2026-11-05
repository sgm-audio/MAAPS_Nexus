import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

    TARGET_CITIES = [
        "Los Angeles",
        "New York",
        "London",
        "Toronto",
        "Nashville",
        "Austin",
        "Atlanta",
        "Vancouver",
        "Chicago",
        "Miami",  # Expanded List
    ]

    SEARCH_QUERY = "Audio Post Production Studio"

    @classmethod
    def validate(cls):
        missing = []
        if not cls.GROQ_API_KEY:
            missing.append("GROQ_API_KEY")
        if not cls.SMTP_USER:
            missing.append("SMTP_USER")

        if missing:
            print(f"⚠️  WARNING: Missing Keys: {', '.join(missing)}")
            return False
        return True
