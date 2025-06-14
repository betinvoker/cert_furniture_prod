from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, abort, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from app.models import db, Customer, Worker, Organization, Entity, Attribute_entity, Request, Bank, Expertise, Security_requirements, Regulatory_document
from config import Config
from flask import session as flask_session
from werkzeug.utils import secure_filename
import pdfkit
from urllib.parse import quote
from datetime import datetime
import os
# from app import create_app

# app = create_app() # Запуск скрипта создания изменения в БД в соответствии с моделями (app.models)

def format_datetime(value, format="%d.%m.%Y %H:%M"):
    """Форматирует datetime объект в строку"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value
    return value.strftime(format)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = Config.SECRET_KEY

app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'] = Config.UPLOAD_FOLDER_MATERIAL_ENTITY  # Папка для загрузки
app.config['UPLOAD_FOLDER_SECURITY_REQUIREMENTS'] = Config.UPLOAD_FOLDER_SECURITY_REQUIREMENTS # Папка для загрузки файлов с требованиями безопасности
app.config['UPLOAD_FOLDER_REGULATORY_DOCUMENT'] = Config.UPLOAD_FOLDER_REGULATORY_DOCUMENT # Папка для загрузки файлов нормативной документации
app.config['ALLOWED_EXTENSIONS'] = {'docx', 'pdf', 'xlsx'}  # Разрешенные расширения
os.makedirs(app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'], exist_ok=True) # Создаем папку, если ее нет

PDFKIT_CONFIG = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')

# Регистрация фильтра
app.jinja_env.filters['datetimeformat'] = format_datetime

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
    user_type = flask_session.get('user_type')

    if user_type == 'customer':
        return db.session.get(Customer, int(user_id))
    elif user_type == 'worker':
        return db.session.get(Worker, int(user_id))
    return None

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        
        last_name = request.form.get('last_name')
        first_name = request.form.get('first_name')
        patronymic = request.form.get('patronymic')
        phone = request.form.get('phone')
        email = request.form.get('email')

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
        flask_session['login'] = request.form.get('login')
        password = request.form.get('password')
        flask_session['user_type'] = request.form.get('role')

        if flask_session['user_type'] == 'customer':
            customer = Customer.query.filter_by(login=flask_session['login'] ).first()

            if customer and customer.check_password(password):
                login_user(customer)
                return redirect(url_for('profile', login=flask_session['login']))
        
        if flask_session['user_type'] == 'worker':
            worker = Worker.query.filter_by(login=flask_session['login'] ).first()
            
            if worker and worker.check_password(password):
                login_user(worker)
                return redirect(url_for('profile_worker', login=flask_session['login']))

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
    customer = Customer.query.filter_by(login=flask_session['login']).first()

    if not customer:
        return redirect(url_for('login'))
    
    return render_template('profile.html', user=customer)

@app.route("/worker/<login>")
def profile_worker(login):
    worker = Worker.query.filter_by(login=flask_session['login']).first()

    if not worker:
        return redirect(url_for('login'))
    
    return render_template('profile_worker.html', user=worker)

@app.route("/myorganization/<login>")
def my_organization(login):
    customer = Customer.query.filter_by(login=flask_session['login']).first()

    if not customer:
        return redirect(url_for('login'))
    
    organizations = Organization.query.filter_by(id_client=customer.id)

    return render_template('my_organization.html', user=customer, organizations=organizations)

@app.route("/add_myorganization", methods=['POST'])
def add_organization():
    customer = Customer.query.filter_by(login=flask_session['login']).first()

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
        return redirect(url_for('my_organization', login=flask_session['login']))
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
        return redirect(url_for('my_organization', login=flask_session['login']))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/myorganization/delete/<int:id>', methods=['POST'])
def delete_organization(id):
    organization = Organization.query.get_or_404(id)
    db.session.delete(organization)
    db.session.commit()

    return redirect(url_for('my_organization', login=flask_session['login']))

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

    o_id_entity = request.form.get('id_entity')
    o_name_attribute = request.form.get('name_attribute')
    o_description = request.form.get('description')

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
    customer = Customer.query.filter_by(login=flask_session['login']).first()
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
        customer = Customer.query.filter_by(login=flask_session['login']).first()
        organizations = Organization.query.filter_by(id_client=customer.id).filter(Organization.status!='D').all()
    
        organization_ids = [org.id for org in organizations] 
        entities = Entity.query.filter(Entity.id_organization.in_(organization_ids)).filter(Entity.status!='D').all()

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
        customer = Customer.query.filter_by(login=flask_session['login']).first()
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
    customer = Customer.query.filter_by(login=flask_session['login']).first()

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
    customer = Customer.query.filter_by(login=flask_session['login']).first()
    
    if not customer:
        return redirect(url_for('login'))
    
    myrequest = Request.query.get(id)
    organizations = Organization.query.filter_by(id_client=customer.id).filter(Organization.status!='D').all()
    banks = Bank.query.filter(Bank.status!='D').all()
    worker = Worker.query.get(myrequest.id_worker)
    organization_ids = [org.id for org in organizations]
    entities = Entity.query.filter(Entity.id_organization.in_(organization_ids)).filter(Entity.status!='D').all()
    attributes_entity = Attribute_entity.query.filter(Attribute_entity.id_entity==myrequest.id_entity).filter(Attribute_entity.status!='D').all()
    
    return render_template('request.html', organizations=organizations, entities=entities, request=myrequest, banks=banks, worker=worker, attributes=attributes_entity)

@app.route('/request/update/<int:id>', methods=['POST'])
def update_request(id):
    try:
        customer = Customer.query.filter_by(login=flask_session['login']).first()
    
        if not customer:
            return redirect(url_for('login'))
        
        o_request = Request.query.get_or_404(id)
        
        o_request.id_entity = request.form.get('exampleSelectUpdateEntity')
        o_request.id_bank = request.form.get('exampleSelectUpdateBank')
        o_request.okved = request.form.get('exampleUpdateOKVED')
        o_request.account = request.form.get('exampleAccount')
        o_request.phone = request.form.get('examplePhone')
        o_request.status_request = 'Зарегистрирована'

        # Обработка файла
        file = request.files['formMaterialEntity']
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER_MATERIAL_ENTITY'], filename))
            o_request.link_material = filename

        db.session.commit()

        flash("Информация о заявке обновлена!")
        return redirect(url_for('myrequest', id=o_request.id))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/request/delete/<int:id>', methods=['POST'])
def delete_request(id):
    try:
        customer = Customer.query.filter_by(login=flask_session['login']).first()
    
        if not customer:
            return redirect(url_for('login'))
    
        request = Request.query.get_or_404(id)

        request.status = 'D'

        db.session.commit()

        flash("Информация о заявке удалена!")
        return redirect(url_for('requests'))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/generate_pdf_request/<int:id>', methods=['GET'])
def generate_pdf_request(id):
    try:
        myrequest = Request.query.get_or_404(id)
        entity = db.session.get(Entity, myrequest.id_entity)
        organization = db.session.get(Organization, entity.id_organization)
        bank = db.session.get(Bank, myrequest.id_bank)
        customer = db.session.get(Customer, organization.id_client)
        worker = db.session.get(Worker, myrequest.id_worker) if myrequest.id_worker else None
        attributes = Attribute_entity.query.filter(Attribute_entity.id_entity==entity.id, Attribute_entity.status != 'D').all()

        template_context = {
            'request_obj': myrequest
            ,'customer': customer
            ,'entity': entity
            ,'org': organization
            ,'bank': bank
            ,'worker': worker
            ,'attrs': attributes
            ,'creation_date': myrequest.date_create
            ,'title': f'#{myrequest.id}. Заявка на экспертизу {entity.name}'
        }

        # Рендерим HTML шаблон
        html = render_template('report.html', **template_context)
        # Конвертируем HTML в PDF
        options = {
            'footer-center': '[page]/[topage]',
            'footer-font-size': '10',
            'footer-spacing': '5'
        }

        pdf = pdfkit.from_string(html, False, configuration=PDFKIT_CONFIG, options=options)
        
        # Генерация имени файла с кодированием
        filename = f"request_{myrequest.id}_{entity.name}.pdf"
        safe_filename = quote(filename, safe='')  # Кодируем спецсимволы

        # Создаем ответ
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=request_{safe_filename}_{quote(entity.name)}.pdf'
        return response
    
    except Exception as e:
        app.logger.error(f"Error generating PDF: {str(e)}")
        return "Ошибка при генерации PDF", 500

@app.route('/all_requests', methods=['GET'])
def requests_worker():
    worker = Worker.query.filter_by(login=flask_session['login']).first()

    if not worker:
        return redirect(url_for('login'))

    organizations = Organization.query.filter(Organization.status!='D').all()
    banks = Bank.query.filter(Bank.status!='D').all()
    workers = Worker.query.filter(Worker.status!='D').all()
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

    selectWorker = request.args.get('floatingSelectWorker', '')
    if selectWorker:
        selectWorker = selectWorker.strip()
        query = query.filter(Request.id_worker == str(selectWorker))
            
    requests = query.filter(Request.status!='D').all()

    return render_template('requests.html', organizations=organizations, entities=entities, requests=requests, banks=banks, workers=workers)

@app.route('/all_requests/request/<int:id>', methods=['GET'])
def request_worker(id):
    worker = Worker.query.filter_by(login=flask_session['login']).first()

    if not worker:
        return redirect(url_for('login'))
    
    req = Request.query.get(id)
    entity = Entity.query.filter(Entity.id==req.id_entity, Entity.status!='D').first()
    organization = Organization.query.filter(Organization.id==entity.id_organization, Organization.status!='D').first()
    worker = Worker.query.get(req.id_worker)
    bank = Bank.query.filter(Bank.id==req.id_bank, Bank.status!='D').all()
    attributes_entity = Attribute_entity.query.filter(Attribute_entity.id_entity==req.id_entity, Attribute_entity.status!='D').all()
    
    return render_template('request.html', organization=organization, entity=entity, request=req, worker=worker, bank=bank, attributes=attributes_entity)

@app.route('/all_requests/request/update/<int:id>', methods=['POST'])
def accept_request(id):
    try:
        worker = Worker.query.filter_by(login=flask_session['login']).first()
    
        if not worker:
            return redirect(url_for('login'))
    
        o_request = Request.query.get_or_404(id)

        if o_request.id_worker:
            o_request.id_worker = None
        else:
            o_request.id_worker = worker.id
        
        o_request.status_request = request.form.get('exampleSelectUpdateRequestStatus') if request.form.get('exampleSelectUpdateRequestStatus') else o_request.status_request

        db.session.commit()

        flash("По заявке назначен эксперт или изменен статус заявки!")
        return redirect(url_for('request_worker', id=o_request.id))
    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/expertises', methods=['GET'])
def expertises():
    worker = Worker.query.filter_by(login=flask_session['login']).first()
    
    if not worker:
        return redirect(url_for('login'))
    
    query = Expertise.query.filter(Expertise.id_worker==worker.id, Expertise.status!='D')

    expertises_list = query.all()
    requests_ids = [exp.id_request for exp in expertises_list]
    requests = Request.query.filter(Request.id.in_(requests_ids), Request.status!='D').all()
    
    entity_ids = [req.id_entity for req in requests]
    entities = Entity.query.filter(Entity.id.in_(entity_ids), Entity.status!='D').all()

    organization_ids = [entity.id_organization for entity in entities]
    organizations = Organization.query.filter(Organization.id.in_(organization_ids), Organization.status!='D').all()

    search = request.args.get('exampleFormControlSearch', '').strip()
    if search:
        if search.isdigit():
            query = query.join(Request).filter(Request.id_entity == int(search))

    selectStatusExpertis = request.args.get('floatingSelectStatusExpertis', '')
    if selectStatusExpertis:
        query = query.filter(Expertise.status_request==str(selectStatusExpertis))
            
    expertises = query.filter(Expertise.status!='D').all()
   
    data = {
        'worker': worker
        ,'expertises': expertises
        ,'requests': requests
        ,'entities': entities
        ,'organizations': organizations
    }

    return render_template('expertises.html', **data)

@app.route('/expertises/expertise/<int:id>', methods=['GET'])
def expertise(id):
    worker = Worker.query.filter_by(login=flask_session['login']).first()

    if not worker:
        return redirect(url_for('login'))

    expertise = Expertise.query.get(id)
    req = Request.query.filter(Request.id==expertise.id_request).first()
    entity = Entity.query.filter(Entity.id==req.id_entity).first()
    security_requirements = Security_requirements.query.filter(Security_requirements.status!='D').all()
    regulatory_documents = Regulatory_document.query.filter(Regulatory_document.status!='D').all()
    attribute_entities = Attribute_entity.query.filter(Attribute_entity.id_entity==entity.id, Entity.status!='D').all()
    workers = Worker.query.filter(Worker.status!='D').all()

    data = {
        'worker': worker
        ,'expertise': expertise
        ,'request': req
        ,'entity': entity
        ,'security_requirements': security_requirements
        ,'regulatory_documents': regulatory_documents
        ,'attribute_entities': attribute_entities
        ,'workers': workers
    }

    return render_template('expertise.html', **data)    

@app.route('/expertise/update/<int:id>', methods=['POST'])
def update_expertise(id):
    try:
        worker = Worker.query.filter_by(login=flask_session['login']).first()
    
        if not worker:
            return redirect(url_for('login'))
        
        o_expertise = Expertise.query.get_or_404(id)    
        o_expertise.status_request = request.form.get('exampleSelectUpdateExpertiseStatus') if request.form.get('exampleSelectUpdateExpertiseStatus') else o_expertise.status_request
        o_expertise.id_worker = request.form.get('exampleSelectUpdateWorker') if request.form.get('exampleSelectUpdateWorker') else o_expertise.id_worker
        o_expertise.link_inference = request.form.get('exampleUpdateLinkInference') if request.form.get('exampleUpdateLinkInference') else o_expertise.link_inference
        
        if request.form.get('exampleSelectUpdateSecurityRequirements') in ('', 'None', None):
            o_expertise.id_security_requirements = None
        else:
            o_expertise.id_security_requirements = request.form.get('exampleSelectUpdateSecurityRequirements')

        if request.form.get('exampleSelectUpdateRegulatoryDocuments') in ('', 'None', None):
            o_expertise.id_regulatory_document = None
        else:
            o_expertise.id_regulatory_document = request.form.get('exampleSelectUpdateRegulatoryDocuments')

        db.session.commit()

        flash("Информация об экспертизе была изменена!")
        return redirect(url_for('expertise', id=o_expertise.id))

    except Exception as e:
        db.session.rollback()
        return f"Ошибка записи: {e}", 500

@app.route('/generate_pdf_expertise/<int:id>', methods=['GET'])
def generate_pdf_expertise(id):
    try:
        expertise = Expertise.query.get_or_404(id)
        req = db.session.get(Request, expertise.id_request)
        entity = db.session.get(Entity, req.id_entity)
        organization = db.session.get(Organization, entity.id_organization)
        worker = db.session.get(Worker, expertise.id_worker) if expertise.id_worker else None
        attributes = Attribute_entity.query.filter(Attribute_entity.id_entity==entity.id, Attribute_entity.status != 'D').all()
        regulatory_document = db.session.get(Regulatory_document, expertise.id_regulatory_document)
        security_requirement = db.session.get(Security_requirements, expertise.id_security_requirements)
        user_type = flask_session.get('user_type')

        template_context = {
            'expertise': expertise
            ,'request': req
            ,'entity': entity
            ,'org': organization
            ,'worker': worker
            ,'attrs': attributes
            ,'regulatory_document': regulatory_document
            ,'security_requirement': security_requirement
            ,'creation_date': expertise.date_create
            ,'role': user_type
            ,'title': f'#{ expertise.id }. Экспертиза объекта { entity.name }'
        }

        # Рендерим HTML шаблон
        html = render_template('expertise_report.html', **template_context)
        # Конвертируем HTML в PDF
        options = {
            'footer-center': '[page]/[topage]',
            'footer-font-size': '10',
            'footer-spacing': '5'
        }

        pdf = pdfkit.from_string(html, False, configuration=PDFKIT_CONFIG, options=options)
        
        # Генерация имени файла с кодированием
        filename = f"expertise_{expertise.id}_for_{entity.name}.pdf"
        safe_filename = quote(filename, safe='')  # Кодируем спецсимволы

        # Создаем ответ
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename=expertise_{safe_filename}_{quote(entity.name)}.pdf'
        return response
    
    except Exception as e:
        app.logger.error(f"Error generating PDF: {str(e)}")
        return "Ошибка при генерации PDF", 500

@app.route('/myexpertises', methods=['GET'])
def myexpertises():
    customer = Customer.query.filter_by(login=flask_session['login']).first()
    
    if not customer:
        return redirect(url_for('login'))
    
    organizations = Organization.query.filter(Organization.id_client==customer.id, Organization.status!='D').all()
    
    entities_ids = [org.id for org in organizations]
    entities = Entity.query.filter(Entity.id.in_(entities_ids), Entity.status!='D').all()

    requests_ids = [ent.id for ent in entities]
    requests = Request.query.filter(Request.id.in_(requests_ids), Request.status!='D').all()

    expertises_ids = [req.id for req in requests]
    query = db.session.query(Expertise).filter(Expertise.id_request.in_(expertises_ids), Expertise.status!='D')

    # search = request.args.get('exampleFormControlSearch', '').strip()
    # if search:
    #     if search.isdigit():
    #         query = query.join(Request).filter(Request.id_entity == int(search), Expertise.status!='D')

    # selectStatusExpertis = request.args.get('floatingSelectStatusExpertis', '')
    # if selectStatusExpertis:
    #     query = query.filter(Expertise.status_request==str(selectStatusExpertis), Expertise.status!='D')
            
    # expertises = query.all()
    expertises = Expertise.query.filter(Expertise.id_request.in_(expertises_ids), Expertise.status!='D').all()
   
    data = {
        'expertises': expertises
        ,'requests': requests
        ,'entities': entities
        ,'organizations': organizations
    }

    return render_template('myexpertises.html', **data)

if __name__ == "__main__":
    app.run(debug=True)