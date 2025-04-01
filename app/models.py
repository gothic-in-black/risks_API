from . import db


class Patients(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(8), nullable=False)
    snils = db.Column(db.String, nullable=False)
    id_firm = db.Column(db.Integer, nullable=False)


class Research(db.Model):
    __tablename__ = 'research'
    id = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.Integer, nullable=False)
    id_patient = db.Column(db.Integer, nullable=False)
    id_firm = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    name = db.Column(db.String, nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(8), nullable=False)
    cholesterol = db.Column(db.Float, nullable=True)
    blood_pressure = db.Column(db.SmallInteger, nullable=True)
    smoking = db.Column(db.SmallInteger, nullable=False)
    diastolic_bp = db.Column(db.SmallInteger, nullable=True)
    systolic_bp = db.Column(db.SmallInteger, nullable=True)
    pulse = db.Column(db.SmallInteger, nullable=True)


class Risk(db.Model):
    __tablename__ = 'risk'
    id = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.Integer, nullable=False)
    risk = db.Column(db.Float, nullable=False)
    id_patient = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String, nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    id_firm = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)