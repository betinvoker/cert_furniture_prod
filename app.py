from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from app.models import db, Customer, Worker, Organization, Entity, Attribute_entity, Request, Bank
from config import Config
from flask import session
from werkzeug.utils import secure_filename
import os
# from app import create_app

# app = create_app() # Запуск скрипта создания изменения в БД в соответствии с моделями (app.models)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = Config.SECRET_KEY

app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'] = './static/material_entity'  # Папка для загрузки
app.config['ALLOWED_EXTENSIONS'] = {'docx', 'pdf', 'xlsx'}  # Разрешенные расширения
os.makedirs(app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'], exist_ok=True) # Создаем папку, если ее нет

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/download/<filename>')
def download_file(filename):
    try:
        # Проверяем безопасное имя файла
        safe_filename = secure_filename(filename)
        if not safe_filename:
            abort(404)
            
        # Полный путь к файлу
        file_path = os.path.join(app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'], safe_filename)
        
        # Проверяем существование файла
        if not os.path.isfile(file_path):
            abort(404)
            
        return send_from_directory(
            app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'],
            safe_filename,
            as_attachment=True,
            download_name=safe_filename  # Имя файла для скачивания
        )
    except Exception as e:
        abort(500)

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

@app.route("/organizations/entities", methods=['GET'])
def entities():
    customer = Customer.query.filter_by(login=session['login']).first()
    organizations = Organization.query.filter_by(id_client=customer.id).filter(Organization.status!='D').all()
    organization_ids = [org.id for org in organizations]
    query = Entity.query.filter(Entity.id_organization.in_(organization_ids)).filter(Entity.status!='D')

    search = request.args.get('exampleFormControlSearch', '')
    if search:
        if search.isdigit():
            query = query.filter(Entity.id == int(search))
        else:
            query = query.filter(Entity.name.ilike(f'%{search}%'))

    entities = query.filter(Entity.status!='D').all()

    return render_template('entities.html', organizations=organizations, entities=entities)

@app.route('/entity/update/<int:id>', methods=['POST'])
def update_entity(id):
    try:
        entity = Entity.query.get_or_404(id)
        customer = Customer.query.filter_by(login=session['login']).first()
        organizations = Organization.query.filter_by(id_client=customer.id).filter(Organization.status!='D').all()
    
        organization_ids = [org.id for org in organizations] 
        entities = Entity.query.filter(Entity.id_organization.in_(organization_ids)).filter(Entity.status!='D').all()
        print(request.form['exampleUpdateNameEntity'], request.form['exampleSelectUpdateOrganizations'])
        entity.name = request.form['exampleUpdateNameEntity']
        entity.id_organization = request.form['exampleSelectUpdateOrganizations']

        db.session.commit()

        flash("Информация об объекте обновлена!")
        return redirect(url_for('entities', organizations=organizations, entities=entities))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/entity/delete/<int:id>', methods=['POST'])
def delete_entity(id):
    try:
        entity = Entity.query.get_or_404(id)
        customer = Customer.query.filter_by(login=session['login']).first()
        organizations = Organization.query.filter_by(id_client=customer.id).filter(Organization.status!='D').all()
    
        organization_ids = [org.id for org in organizations] 
        entities = Entity.query.filter(Entity.id_organization.in_(organization_ids)).filter(Entity.status!='D').all()

        entity.status = 'D'

        db.session.commit()

        flash("Информация об объекте удалена!")
        return redirect(url_for('entities', organizations=organizations, entities=entities))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/requests', methods=['GET'])
def requests():
    customer = Customer.query.filter_by(login=session['login']).first()

    if not customer:
        return redirect(url_for('login'))

    organizations = Organization.query.filter_by(id_client=customer.id).filter(Organization.status!='D').all()
    banks = Bank.query.filter(Bank.status!='D').all()
    organization_ids = [org.id for org in organizations]
    entities = Entity.query.filter(Entity.id_organization.in_(organization_ids)).filter(Entity.status!='D').all()
    entity_ids = [ent.id for ent in entities]
    query = Request.query.filter(Request.id_entity.in_(entity_ids), Request.status!='D')

    search = request.args.get('exampleFormControlSearch', '').strip()
    if search:
        if search.isdigit():
            query = query.filter(Request.id == int(search))
        else:
            query = query.filter(Request.id_entity == int(search))

    selectOrganization = request.args.get('floatingSelectOrganization', '')
    if selectOrganization:
        if selectOrganization.isdigit():
            query = query.filter(Request.id_entity == Entity.id).filter(Entity.id_organization == int(selectOrganization))

    selectStatusRequest = request.args.get('floatingSelectStatusRequest', '')
    if selectStatusRequest:
        selectStatusRequest = selectStatusRequest.strip()
        query = query.filter(Request.status_request == str(selectStatusRequest))
            
    requests = query.filter(Request.status!='D').all()

    return render_template('requests.html', organizations=organizations, entities=entities, requests=requests, banks=banks)

@app.route("/requests/add_request", methods=['POST'])
def add_request():
    o_id_entity = request.form['exampleSelectEntity']
    o_id_bank = request.form['exampleSelectBank']
    o_account = request.form['exampleAccount']
    o_okved = request.form['exampleOKVED']
    o_phone = request.form['examplePhone']

    file = request.files['formMaterialEntity']
        
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'], filename))

    try:
        new_request = Request(id_entity = o_id_entity, id_bank = o_id_bank, account = o_account, okved = o_okved, phone = o_phone, link_material = filename)
        db.session.add(new_request)
        db.session.commit()

        flash("Заявка на экспертизу добавлена!")
        return redirect(url_for('requests'))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/requests/request/<int:id>', methods=['GET'])
def myrequest(id):
    customer = Customer.query.filter_by(login=session['login']).first()
    
    if not customer:
        return redirect(url_for('login'))
    
    myrequest = Request.query.get(id)
    organizations = Organization.query.filter_by(id_client=customer.id).filter(Organization.status!='D').all()
    banks = Bank.query.filter(Bank.status!='D').all()
    organization_ids = [org.id for org in organizations]
    entities = Entity.query.filter(Entity.id_organization.in_(organization_ids)).filter(Entity.status!='D').all()
    attributes_entity = Attribute_entity.query.filter(Attribute_entity.id_entity==myrequest.id_entity).filter(Attribute_entity.status!='D').all()
    
    return render_template('request.html', organizations=organizations, entities=entities, request=myrequest, banks=banks, attributes=attributes_entity)

if __name__ == "__main__":
    app.run(debug=True)