from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Customer, Worker, Organization, Entity, Attribute_entity
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

    return render_template('my_organization.html', user=customer, organizations=organizations)

@app.route("/add_myorganization", methods=['POST'])
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

@app.route("/myorganization/update/<int:id>")
def update_organization(id):
    organization = Organization.query.get_or_404(id)
    return render_template('update_organization.html', organization=organization)

@app.route('/organization/update/<int:id>', methods=['POST'])
def organization_update(id):
    try:
        organization = Organization.query.get(request.form['id'])

        organization.name = request.form['name']
        organization.jur_address = request.form['jur_address']
        organization.inn = request.form['inn']
        organization.kpp = request.form['kpp']
        organization.egrul_egrip = request.form['egrul_egrip']
        organization.phone = request.form['phone']
        organization.email = request.form['email']

        db.session.commit()

        flash("Информация об организации обновлена!")
        return redirect(url_for('my_organization', login=session['login']))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/myorganization/delete/<int:id>', methods=['POST'])
def delete_organization(id):
    organization = Organization.query.get_or_404(id)
    db.session.delete(organization)
    db.session.commit()

    return redirect(url_for('my_organization', login=session['login']))

@app.route("/myorganization/organization/<int:id>")
def organization(id):
    organization = Organization.query.get_or_404(id)
    entities = Entity.query.filter_by(id_organization=organization.id)

    id_entity = [entity.id for entity in entities]
    attribute_entities = Attribute_entity.query.filter(Attribute_entity.id_entity.in_(id_entity)).filter(Attribute_entity.status!='D')

    return render_template('organization.html', organization=organization, entities=entities, attribute_entities=attribute_entities)

@app.route("/add_entity/<int:id>", methods=['POST'])
def add_entity(id):
    organization = Organization.query.get_or_404(id)

    o_name = request.form['name']

    try:
        new_entity = Entity(id_organization = organization.id, name = o_name)
        db.session.add(new_entity)
        db.session.commit()

        flash("Объект добавлен!")
        return redirect(url_for('organization', id=organization.id))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route("/organization/add_attribute_entity/<int:id>", methods=['POST'])
def add_attribute_entity(id):
    organization = Organization.query.get_or_404(id)

    o_id_entity = request.form['id_entity']
    o_name_attribute = request.form['name_attribute']
    o_description = request.form['description']

    try:
        new_attribute = Attribute_entity(id_entity = o_id_entity, name_attribute = o_name_attribute, description = o_description)
        db.session.add(new_attribute)
        db.session.commit()

        flash("Атрибут добавлен!")
        return redirect(url_for('organization', id=organization.id))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route("/organization/add_attribute/<int:id>", methods=['POST'])
def add_attribute(id):
    organization = Organization.query.get_or_404(id)

    o_id_entity = request.form['id_entity']
    o_name_attribute = request.form['name_attribute']
    o_description = request.form['description']

    try:
        new_attribute = Attribute_entity(id_entity = o_id_entity, name_attribute = o_name_attribute, description = o_description)
        db.session.add(new_attribute)
        db.session.commit()

        flash("Атрибут добавлен!")
        return redirect(url_for('entity', id_organization=organization.id, id_entity=o_id_entity))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/attribute/update/<int:id>', methods=['POST'])
def update_attribute(id):
    try:
        attribute = Attribute_entity.query.get_or_404(id)
        entity = Entity.query.get_or_404(attribute.id_entity)
        organization = Organization.query.get_or_404(entity.id_organization)

        attribute.name_attribute = request.form['exampleUpdateNameAttribute']
        attribute.description = request.form['exampleFormControlTextareaUpdateDescription']

        db.session.commit()

        flash("Информация о характеристике объекта обновлена!")
        return redirect(url_for('entity', id_organization=organization.id, id_entity=entity.id))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/attribute/delete/<int:id>', methods=['POST'])
def delete_attribute(id):
    try:
        attribute = Attribute_entity.query.get_or_404(id)
        entity = Entity.query.get_or_404(attribute.id_entity)
        organization = Organization.query.get_or_404(entity.id_organization)

        attribute.status = 'D'

        db.session.commit()

        flash("Информация о характеристике объекта удалена!")
        return redirect(url_for('entity', id_organization=organization.id, id_entity=entity.id))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route("/organization/<int:id_organization>/entity/<int:id_entity>")
def entity(id_organization, id_entity):
    organization = Organization.query.get_or_404(id_organization)
    entity = Entity.query.get_or_404(id_entity)
    attributes = Attribute_entity.query.filter_by(id_entity=entity.id).filter(Attribute_entity.status!='D')

    return render_template('entity.html', organization=organization, entity=entity, attributes=attributes)

if __name__ == "__main__":
    app.run(debug=True)