from app import db
from datetime import datetime

class Customer(db.Model):
    __tablename__ = 'customer'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    last_name = db.Column(db.String(1024), nullable=False, doc='Фамилия')
    first_name = db.Column(db.String(1024), nullable=False, doc='Имя')
    patronymic = db.Column(db.String(1024), nullable=True, doc='Отчество')
    login = db.Column(db.String(129), unique=True, doc='Login')
    password = db.Column(db.String(256), nullable=False, doc='Password')
    phone = db.Column(db.String(12), nullable=False, doc='Номер телефона')
    email = db.Column(db.String(1024), nullable=True, doc='Электронная почта')

    def __repr__(self):
        return f"<Customer {self.id}, {self.login}, {self.last_name}, {self.first_name}>"
    
class Organization(db.Model):
    __tablename__ = 'organization'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    id_client = db.Column(db.Integer, db.ForeignKey('customer.id'), doc='ID Customer')
    name = db.Column(db.String(1024), nullable=False, doc='Наименование организации')
    jur_address = db.Column(db.String(1024), nullable=False, doc='Юридический адрес')
    inn = db.Column(db.String(12), nullable=True, doc='ИНН')
    kpp = db.Column(db.String(9), nullable=True, doc='КПП')
    egrul_egrip = db.Column(db.String(13), nullable=True, doc='ЕГРЮЛ или ЕГРИП')
    phone = db.Column(db.String(12), nullable=True, doc='Номер телефона')
    email = db.Column(db.String(1024), nullable=True, doc='Электронная почта')

    request = db.relationship("Customer", backref=db.backref("customer", uselist=False))

    def __repr__(self):
        return f"<Organization {self.id}, {self.name}, {self.phone}, {self.email}>"
    
class Bank(db.Model):
    __tablename__ = 'bank'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    name = db.Column(db.String(1024), nullable=False, doc='Наименование организации')
    inn = db.Column(db.String(12), nullable=False, doc='ИНН')
    kpp = db.Column(db.String(9), nullable=False, doc='КПП')
    account = db.Column(db.String(20), nullable=False, doc='Корреспондентский счет')
    okved = db.Column(db.String(6), nullable=True, doc='ОКВЭД')

    def __repr__(self):
        return f"<Bank {self.id}, {self.name}, {self.account}, {self.okved}>"
    
class Object(db.Model):
    __tablename__ = 'object'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    name = db.Column(db.String(1024), nullable=False, doc='Наименование организации')
    id_organization = db.Column(db.Integer, db.ForeignKey('organization.id'), doc='ID Organization')
    
    request = db.relationship("Organization", backref=db.backref("organization", uselist=False))

    def __repr__(self):
        return f"<Bank {self.id}, {self.name}>"

class Attribute_object(db.Model):
    __tablename__ = 'attribute_object'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    id_object = db.Column(db.Integer, db.ForeignKey('object.id'), doc='ID Object')
    description = db.Column(db.String(2048), nullable=False, doc='Описание технической характеристики')

    request = db.relationship("Object", backref=db.backref("object", uselist=False))

    def __repr__(self):
        return f"<Attribute_object {self.id}, {self.id_object}>"
    
class Picture_object(db.Model):
    __tablename__ = 'picture_object'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    id_object = db.Column(db.Integer, db.ForeignKey('object.id'), doc='ID Object')
    link_picture = db.Column(db.String(2048), nullable=False, doc='Ссылка на изображение объекта')

    request = db.relationship("Picture_object", backref=db.backref("object", uselist=False))

    def __repr__(self):
        return f"<Picture_object {self.id}, {self.id_object}>"
    
class Regulatory_document(db.Model):
    __tablename__ = 'regulatory_document'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    name = db.Column(db.String(1024), nullable=False, doc='Наименование')
    description = db.Column(db.String(4096), nullable=True, doc='Описание')
    link_material = db.Column(db.String(4096), nullable=False, doc='Ссылка на изображение объекта')

    def __repr__(self):
        return f"<Regulatory_document {self.id}, {self.name}>"

class Security_requirements(db.Model):
    __tablename__ = 'security_requirements'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    name = db.Column(db.String(1024), nullable=False, doc='Наименование')
    method = db.Column(db.String(4096), nullable=False, doc='Метод испытания')
    measure = db.Column(db.String(10), nullable=True, doc='Единица измерения')
    link_material = db.Column(db.String(4096), nullable=False, doc='Ссылка на нормативные документы')

    def __repr__(self):
        return f"<Security_requirements {self.id}, {self.name}>"

class Worker(db.Model):
    __tablename__ = 'worker'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    last_name = db.Column(db.String(1024), nullable=False, doc='Фамилия')
    first_name = db.Column(db.String(1024), nullable=False, doc='Имя')
    patronymic = db.Column(db.String(1024), nullable=True, doc='Отчество')
    login = db.Column(db.String(129), unique=True, doc='Login')
    password = db.Column(db.String(256), nullable=False, doc='Password')
    phone = db.Column(db.String(12), nullable=False, doc='Номер телефона')
    email = db.Column(db.String(1024), nullable=True, doc='Электронная почта')
    position = db.Column(db.String(256), nullable=False, doc='Должность')

    def __repr__(self):
        return f"<Worker {self.id}, {self.login}, {self.position}, {self.last_name}, {self.first_name}>"

class Request(db.Model):
    __tablename__ = 'request'
    id = db.Column(db.Integer, primary_key=True, doc='Первичный ключ')
    date_create = db.Column(db.DateTime, default=datetime.now, doc='Дата создания/изменения статуса')
    status = db.Column(db.String(1), default='I', doc='Статус (I/U/D)')
    id_worker = db.Column(db.Integer, db.ForeignKey('worker.id'), doc='ID Worker')
    id_object = db.Column(db.Integer, db.ForeignKey('object.id'), doc='ID Object')
    status_request = db.Column(db.String(1), default='I', doc='Статус (Зарегистрирована/ В работе / Отклонена/ Выполнена)')
    link_material = db.Column(db.String(4096), nullable=False, doc='Документация изготовителя')
    okved = db.Column(db.String(6), nullable=True, doc='ОКВЭД')
    id_bank = db.Column(db.Integer, db.ForeignKey('bank.id'), doc='ID Bank')
    account = db.Column(db.String(20), nullable=False, doc='Корреспондентский счет')
    phone = db.Column(db.String(12), nullable=False, doc='Номер телефона для обратной связи')

    request = db.relationship("Worker", backref=db.backref("worker", uselist=False))
    request = db.relationship("Object", backref=db.backref("object", uselist=False))
    request = db.relationship("Bank", backref=db.backref("bank", uselist=False))

    def __repr__(self):
        return f"<Request {self.id}, {self.name}>"

# class Expertise(db.Model):
#     __tablename__ = 'expertise'
#     pass