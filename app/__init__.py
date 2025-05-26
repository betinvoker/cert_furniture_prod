from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    from app import models

    return app

# Инициализируй Alembic (один раз)
# flask db init

# Создай миграции из моделей
# flask db migrate -m "Initial migration"

# Применить миграции в PostgreSQL
# flask db upgrade