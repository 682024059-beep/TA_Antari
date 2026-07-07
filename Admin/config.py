import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    PORT = int(os.getenv("PORT", 4000))
    FLASK_ENV = os.getenv("FLASK_ENV", "production")
    CORS_ORIGIN = os.getenv("CORS_ORIGIN", "*")
    SECRET_KEY = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET", "dev-secret-change-me"))

    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 3306))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "antari_pos")
    DB_SSL = os.getenv("DB_SSL", "false").lower() == "true"

    JWT_SECRET = os.getenv("JWT_SECRET", SECRET_KEY)
    JWT_EXPIRES_HOURS = int(os.getenv("JWT_EXPIRES_HOURS", 8))

    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")

    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "ANTARI CoffeeShop <onboarding@resend.dev>")
    RESEND_ADMIN_EMAIL = os.getenv("RESEND_ADMIN_EMAIL")
