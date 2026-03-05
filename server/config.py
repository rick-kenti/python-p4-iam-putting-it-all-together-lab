# config.py
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_bcrypt import Bcrypt
from flask_restful import Api
from sqlalchemy import MetaData

metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

# Extensions (initialized later)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
bcrypt = Bcrypt()
api = Api()