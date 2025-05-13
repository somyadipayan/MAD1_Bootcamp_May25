class Config:
    SECRET_KEY = 'mysecretkey'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///library.sqlite3'
    SQLALCHEMY_TRACK_MODIFICATIONS = False