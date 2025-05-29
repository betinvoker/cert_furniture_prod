from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Customer, Worker, Organization
from config import Config
from flask import session
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
def load_user(user_id):
    user_type = session.get('user_type')

    if user_type == 'customer':
        return db.session.get(Customer, int(user_id))
    elif user_type == 'worker':
        return db.session.get(Worker, int(user_id))
    return None

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

        if Customer.query.filter_by(login=login).first() | Worker.query.filter_by(login=login).first():
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
        session['login'] = request.form['login']
        password = request.form['password']
        session['user_type'] = request.form['role']

        if session['user_type'] == 'customer':
            customer = Customer.query.filter_by(login=session['login']).first()

            if customer and customer.check_password(password):
                login_user(customer)
                return redirect(url_for('profile', login=session['login']))
            
        if session['user_type'] == 'worker':
            worker = Worker.query.filter_by(login=session['login']).first()
            
            if worker and worker.check_password(password):
                login_user(worker)
                return redirect(url_for('profile_worker', login=session['login']))

        flash('Неверные логин или пароль')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/profile/<login>")
def profile(login):
    customer = Customer.query.filter_by(login=session['login']).first()
    return render_template('profile.html', user=customer)

@app.route("/worker/<login>")
def profile_worker(login):
    worker = Worker.query.filter_by(login=session['login']).first()
    return render_template('profile_worker.html', user=worker)

@app.route("/myorganization/<login>")
def my_organization(login):
    customer = Customer.query.filter_by(login=session['login']).first()
    organizations = Organization.query.filter_by(id_client=customer.id)
    return render_template('my_organization.html', user=customer, organizations=organizations,)

@app.route('/add_myorganization', methods=['POST'])
def add_organization():
    customer = Customer.query.filter_by(login=session['login']).first()

    o_name = request.form['name']
    o_jur_address = request.form['jur_address']
    o_inn = request.form['inn']
    o_kpp = request.form['kpp']
    o_egrul_egrip = request.form['egrul_egrip']
    o_phone = request.form['phone']
    o_email = request.form['email']

    try:
        new_organization = Organization(id_client = customer.id, name = o_name, jur_address = o_jur_address, inn = o_inn, kpp = o_kpp, egrul_egrip = o_egrul_egrip, phone = o_phone, email = o_email)
        db.session.add(new_organization)
        db.session.commit()

        flash("Организация добавлена!")
        return redirect(url_for('my_organization', login=session['login']))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

from flask import request, flash, redirect, url_for

@app.route('/myorganization/<int:id>/update', methods=['POST'])
def update_organization(id):
    id = request.form.get('id')
    organization = Organization.query.get_or_404(id)
    
    # Сохраняем старые значения для отображения в случае ошибки
    old_name = organization.name
    old_jur_address = organization.jur_address
    old_inn = organization.inn
    old_kpp = organization.kpp
    old_egrul_egrip = organization.egrul_egrip
    old_phone = organization.phone
    old_email = organization.email
    
    try:
        organization.name = request.form.get('name')
        organization.jur_address = request.form.get('jur_address')
        organization.inn = request.form.get('inn')
        organization.kpp = request.form.get('kpp')
        organization.egrul_egrip = request.form.get('egrul_egrip')
        organization.phone = request.form.get('phone')
        organization.email = request.form.get('email')

        db.session.commit()
        flash('Изменения успешно сохранены!', 'success')
    except Exception as e:
        db.session.rollback()
        # Возвращаем старые значения при ошибке
        organization.title = old_name
        organization.description = old_jur_address
        organization.description = old_inn
        organization.description = old_kpp
        organization.description = old_egrul_egrip
        organization.description = old_phone
        organization.description = old_email

        flash(f'Ошибка при сохранении: {str(e)}', 'danger')
    
    return redirect(url_for('my_organization', login=session['login']))

@app.route('/myorganization/<int:id>/delete', methods=['POST'])
def delete_organization(id):
    organization = Organization.query.get_or_404(id)
    db.session.delete(organization)
    db.session.commit()

    return redirect(url_for('my_organization', login=session['login']))

if __name__ == "__main__":
    app.run(debug=True)