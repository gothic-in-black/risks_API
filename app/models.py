from . import db


class Patients(db.Model):
    __tablename__ = 'patients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(8), nullable=False)
    snils = db.Column(db.String, nullable=False)
    id_firm = db.Column(db.Integer, nullable=False)
    smoking = db.Column(db.Boolean, nullable=False)


class Research(db.Model):
    __tablename__ = 'research'
    id = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Date, nullable=False)
    id_patient = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    sex = db.Column(db.String(8), nullable=False)
    smoking = db.Column(db.Boolean, nullable=False)
    cholesterol = db.Column(db.Float, nullable=False)
    ad = db.Column(db.Float, nullable=False)
    id_firm = db.Column(db.Integer, nullable=False)


class Risk(db.Model):
    __tablename__ = 'risk'
    id = db.Column(db.Integer, primary_key=True)
    id_type = db.Column(db.Integer, nullable=False)
    risk = db.Column(db.Float, nullable=False)
    id_patient = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    birthday = db.Column(db.Date, nullable=False)
    id_firm = db.Column(db.Integer, nullable=False)
