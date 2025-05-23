from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Customer
from config import Config
# from app import create_app

# app = create_app() # Запуск скрипта создания изменения в БД в соответствии с моделями (app.models)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = Config.SECRET_KEY
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_customer(user_id):
    return Customer.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']
        
        last_name = request.form['last_name']
        first_name = request.form['first_name']
        patronymic = request.form['patronymic']
        phone = request.form['phone']
        email = request.form['email']

        if Customer.query.filter_by(login=login).first():
            flash('Пользователь уже существует')
            return redirect(url_for('register'))

        customer = Customer(login=login, last_name=last_name, first_name=first_name, patronymic=patronymic, phone=phone, email=email)
        customer.set_password(password)
        db.session.add(customer)
        db.session.commit()
        flash('Регистрация успешна! Войдите.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        customer = Customer.query.filter_by(login=login).first()
        if customer and customer.check_password(password):
            login_user(customer)
            return redirect(url_for('protected'))

        flash('Неверные логин или пароль')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/protected')
@login_required
def protected():
    return f'Привет, {current_user.login}! Это защищённая страница.'

@app.route("/")
def index():
    customers = Customer.query.all()
    return render_template('index.html', customers=customers)

if __name__ == "__main__":
    app.run(debug=True)