import os
import cloudinary


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + BASE_DIR + "/app.db"

cloudinary.config( 
  cloud_name = "skols", 
  api_key = "877892686494448", 
  api_secret = "AkUW2f04FrIMpDK9Q4KPrNzxU7w" 
)