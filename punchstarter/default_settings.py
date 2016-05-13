import os
import cloudinary

DEBUG = os.environ.get("DEBUG", True)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///' + BASE_DIR + '/app.db')
CLOUDINARY_CLOUD_NAME = os.environ.get("CLOUDINARY_CLOUD_NAME", "skols")
CLOUDINARY_API_KEY = os.environ.get("CLOUDINARY_API_KEY", "877892686494448")
CLOUDINARY_API_SECRET = os.environ.get("CLOUDINARY_API_SECRET", "AkUW2f04FrIMpDK9Q4KPrNzxU7w")
MAIL_DEBUG = os.environ.get("MAIL_DEBUG", True)
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_LdxEyCqpQ3aXpuITkNSGVyoS")
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "pk_test_5qlf7YO7hz4RAC4pewtx0qh8")


# For Registration and login after installing Flask-Security
SECURITY_REGISTERABLE = True
SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_EMAIL_SENDER = "Punchstarter"
SECURITY_PASSWORD_HASH = "pbkdf2_sha512"
SECURITY_PASSWORD_SALT = "kjkj98GAT7HJiuuu8.-=88D"

SECRET_KEY = '\xa5\xbc \xfb\xaaws\x8c\x01S~*\x96 \xb2\xa6\xd2r7;\x92\xc0b\x87'

cloudinary.config( 
  cloud_name = CLOUDINARY_CLOUD_NAME, 
  api_key = CLOUDINARY_API_KEY, 
  api_secret = CLOUDINARY_API_SECRET
)