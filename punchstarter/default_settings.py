import os
import cloudinary

DEBUG = os.environ.get("DEBUG", True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + BASE_DIR + '/app.db')
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "skols")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "877892686494448")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "AkUW2f04FrIMpDK9Q4KPrNzxU7w")

cloudinary.config( 
  cloud_name = CLOUDINARY_CLOUD_NAME, 
  api_key = CLOUDINARY_API_KEY, 
  api_secret = CLOUDINARY_API_SECRET
)