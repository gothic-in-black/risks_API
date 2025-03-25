import json
import logging
from flask import jsonify
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from . import db, cache


# Create a logger instance
logger = logging.getLogger(__name__)

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
    try:
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
            logger.info("Check for patient's presence in DB was successful. Name: %s, snils: %s", user, snils)
            return id_patient
    except Exception as e:
        logger.error("Failed to check patient's presence in DB, name: %s, snils: %s. Error: %s", user, snils, str(e))
        return jsonify({'error': "Internal server error"}), 500


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
    try:
        with Session() as session:
            # Insert patient's calculated risk in DB (table 'risks')
            query = text('INSERT INTO risks (id_type, risk, id_patient, name, birthday, id_firm, date) VALUES (:id_type, :risk, :id_patient, :name, :birthday, :id_firm, :date_calculate)')
            session.execute(query, {'id_type': id_type, 'risk': risk, 'id_patient': id_patient, 'name': user, 'birthday': birthday, 'id_firm': id_firm, 'date_calculate': date_calculate})
            session.commit()
            logger.info("Added calculated risk for patient_id: %s to DB", id_patient)
    except Exception as e:
        logger.error("Failed to add calculated risk to DB, patient_id: %s. Error: %s", id_patient, str(e))
        return jsonify({'error': "Internal server error"}), 500


def check_allowed_risks():
    """
    Gets from DB and saves in the cache a dictionary of risk names and their corresponding numerical indices.

    Example of the dict:
        {'type_risk_1': 1, 'type_risk_2': 2}

    Returns (Dict): dictionary of risk names (keys) and their corresponding numerical indices (values).
    """
    # Check cache for risk types
    risk_types = cache.get('risks')
    if risk_types:
        risk_types = json.loads(risk_types)
        logger.info("Risk types loaded from cache successfully.")
    else:
        # Create session to interact with DB
        Session = sessionmaker(bind=db.engine)
        try:
            with Session() as session:
                # Load all rows from table 'type_risk'
                query = text('SELECT * FROM type_risk')
                risk_types_from_db = session.execute(query)

                # Convert Result object to list of dicts.
                # Result (example): risk_dict = {'type': 'type_risk_1', 'id': 1}
                risk_dict = risk_types_from_db.mappings().all()

                # Convert received dicts to format: {'type_risk_1': 1}
                risk_types = {row['type']: row['id'] for row in risk_dict}

                # Store risk types in cache for 24 hours.
                cache.set('risks', json.dumps(risk_types), ex=86400)
                logger.info("Risk types loaded into the cache successfully.")

        except Exception as e:
            logger.error(f"Failed to add 'type_risk' table data to the cache. Error: {str(e)}")
            return jsonify({'error': 'Internal server error'}), 500

    # Return list of dicts with risk types
    return risk_types
