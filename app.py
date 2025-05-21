from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
# from app import create_app

db = SQLAlchemy()
app = Flask(__name__)
# app = create_app() // Запуск скрипта создания изменения в БД в соответствии с моделями (app.models)

@app.route("/")
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)