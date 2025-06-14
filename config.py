class Config:
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:postgres@localhost:5432/postgres'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = '8n7rkmN0a5ZOMhATeo4d'
    UPLOAD_FOLDER_MATERIAL_ENTITY = './static/material_entity'
    UPLOAD_FOLDER_SECURITY_REQUIREMENTS = './regulatory_document'
    UPLOAD_FOLDER_REGULATORY_DOCUMENT = './security_requirements'
