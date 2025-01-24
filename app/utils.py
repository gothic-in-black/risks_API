from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from . import db


def check_patient(id_firm, snils,  user, birthday, gender, **kwargs):
    """
    Checks patient's presence in DB. In case of absence patient in DB, adds him.

    Args:
        - snils (int): Patient's SNILS
        - id_firm (int): Firm ID (passed via decorator @token_required)
        - user (str): Patient's full name
        - birthday (str): Patient's date of birth
        - gender (str): Patient's gender

    Returns: Patient's ID (id_patient)
    """
    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        # Get count of the patients with the equal ID
        query = text('SELECT count(*) FROM patients WHERE snils = :snils AND id_firm = :id_firm')
        result = session.execute(query, {'snils': snils, 'id_firm': id_firm}).scalar()

        if result == 0:
            # Add row in DB with patient's info (name, birthday, gender, snils, id_firm)
            query = text('INSERT INTO patients (name, birthday, gender, snils, id_firm) VALUES (:name, :birthday, :gender, :snils, :id_firm)')
            session.execute(query, {'name': user, 'birthday': birthday, 'gender': gender, 'snils': snils, 'id_firm': id_firm})
            session.commit()

        # Get patient's ID (id_patient)
        query_id_patience = text('SELECT id FROM patients WHERE snils = :snils AND id_firm = :id_firm')
        id_patient = session.execute(query_id_patience, {'snils': snils, 'id_firm': id_firm}).scalar()

        return id_patient


def add_risk(id_type, risk, id_firm, id_patient, user, birthday, **kwargs):
    """
    Adds in DB (table 'risks') calculated risk.
    The same patient but with different medical tests can be presented in the table several times.

    Args:
        - id_type (int): Risk ID
        - risk (float): Calculated risk of the current patient
        - id_patient (int): Patient ID
        - name (str): Patient's full name
        - birthday (datetime): Patient's date of birth
        - firm_id (int): Firm ID (passed via decorator @token_required)

    Returns: None
    """
    # Get date and time of risk calculation
    date_calculate = (datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        # Insert patient's calculated risk in DB (table 'risks')
        query = text('INSERT INTO risks (id_type, risk, id_patient, name, birthday, id_firm, date) VALUES (:id_type, :risk, :id_patient, :name, :birthday, :id_firm, :date_calculate)')
        session.execute(query, {'id_type': id_type, 'risk': risk, 'id_patient': id_patient, 'name': user, 'birthday': birthday, 'id_firm': id_firm, 'date_calculate': date_calculate})
        session.commit()