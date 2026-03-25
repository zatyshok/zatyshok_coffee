import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'zatyshok-cafe-secret-key-2024'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///zatyshok.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # отримати безкоштовно: https://aistudio.google.com/app/apikey
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or 'YOUR_API_KEY_HERE'
    # координати Львова для погодного API
    WEATHER_LAT = 49.8397
    WEATHER_LON = 24.0297
