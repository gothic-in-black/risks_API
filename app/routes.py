import json
import logging
from flask import Blueprint, request, jsonify, make_response
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from datetime import datetime, date
from werkzeug.exceptions import BadRequest

from . import db, limiter, get_id_firm
from .auth import token_required
from .utils import check_patient, add_risk
from validators.CalculateRisk import type_risks


# Create a Blueprint instance named 'routes'
routes = Blueprint('routes', __name__)

#Create a logger instance
logger = logging.getLogger(__name__)

# Error handler for code 400 (Bad request)
@routes.errorhandler(BadRequest)
def bad_request(e):
    id_firm = get_id_firm()
    logger.warning("Bad Request from id_firm %s", id_firm)
    return jsonify({'error': 'Bad Request',
                    'message': "Invalid JSON format. Please check your request.",
                    'timestamp': datetime.now().isoformat()}), 400

# Error handler for status code 429 (Too many requests)
@routes.errorhandler(429)
def ratelimit_error(e):
    id_firm = get_id_firm()
    logging.warning("Too many requests from id_firm %s", id_firm)
    return jsonify({'error': 'Too many requests',
                    'message': "You have exceeded the limit of requests. Please try again later.",
                    'timestamp': datetime.now().isoformat()}), 429

# Error handler for status code 500 (Internal server error)
@routes.errorhandler(500)
def server_error(e):
    logger.error("Internal server error: %s", str(e))
    return jsonify({'error': "Internal server error"}), 500


# Route registration
@routes.route('/niimt/api/v1/patients_list', methods=['GET'])
@limiter.limit("5 per minute")
@token_required
def get_listOfEmployees(id_firm=None):
    """
    Route to get list of employees (patients).

    Method: GET.

    Args:
        - id_firm (int): Firm ID (passed via decorator @token_required).

    Returns (list): List of employees in JSON format.
    """
    firm_id = id_firm
    logger.info('Receiving patient list for firm ID : %s', firm_id)
    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
    try:
        with Session() as session:
            # Select all employees of the firm with current firm_id
            query = text('SELECT name, snils FROM patients WHERE id_firm = :firm_id')
            result = session.execute(query, {'firm_id': firm_id})
            patients = [{'name': row[0], 'snils': row[1]} for row in result]
            logger.info('Successfully received %s patients for firm ID: %s', len(patients), firm_id)

            # Transform patients info in JSON and return it
            response = make_response(json.dumps({'patients': patients}, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'

            return response
    except Exception as e:
        logger.error("Error receiving patient list for firm ID %s: %s", firm_id, str(e))
        return jsonify({'error': "Internal server error"}), 500


@routes.route('/niimt/api/v1/research_list', methods=['GET'])
@limiter.limit("8 per minute")
@token_required
def get_research(id_firm=None):
    """
    Route to get list of research.

    Method: GET.

    Args:
        - id_firm (int): Firm ID (passed via decorator @token_required)
        - dateFrom (str): Start date of the period. Default: '2024-08-01'
        - dateTo (str): Stop date of the period. Default: current date.

    Returns (List): List of research.
    """
    firm_id = id_firm
    logger.info('Receiving research list for firm ID: %s', firm_id)
    # Get dateFrom and dateTo or set default
    dateFrom = request.args.get('dateFrom') or '2024-08-01'
    dateTo = request.args.get('dateTo') or datetime.now().strftime('%Y-%m-%d')

    try:
        # Transform string dateFrom to datetime, set format '%Y-%m-%d 00:00:00'
        dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')
    except ValueError:
        logger.warning('Get invalid dateFrom format from firm ID: %s', firm_id)
        return jsonify({'message': 'dateFrom must be in the format YYYY-MM-DD. Make sure month and day are valid values.'}), 400

    try:
        # Transform string dateTo to datetime, set format '%Y-%m-%d <current_time>'
        dateTo = datetime.strptime(f"{dateTo} {datetime.now().strftime('%H:%M:%S')}", '%Y-%m-%d %H:%M:%S')
    except ValueError:
        logger.warning('Get invalid dateTo format from firm ID: %s', firm_id)
        return jsonify({'message': 'dateTo must be in the format YYYY-MM-DD. Make sure month and day are valid values.'}), 400

    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
    try:
        with Session() as session:
            query = text('SELECT * FROM research LIMIT 1')
            res = session.execute(query)
            column_names = list(res.keys())
            # Select all research for current firm_id between [dateFrom and dateTo]
            query = text('SELECT * FROM research WHERE id_firm = :firm_id AND date BETWEEN :dateFrom AND :dateTo')
            result = session.execute(query, {'firm_id': firm_id, 'dateFrom': dateFrom, 'dateTo': dateTo})

            #Skip first 4 columns in 'research' table: 'id', 'id_firm', 'id_patient', 'id_firm'
            research = [{column_names[i]: row[i] for i in range(4, len(row)) if row[i]} for row in result]
            logger.info('Successfully received %s research lists for firm ID: %s', len(research), firm_id)
            # Transform research info in JSON and return it
            response = make_response(json.dumps({'research': research}, ensure_ascii=False, default=str))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'
            return response
    except Exception as e:
        logger.error("Error receiving research list for firm ID %s: %s", firm_id, str(e))
        return jsonify({'error': "Internal server error"}), 500


@routes.route('/niimt/api/v1/risk_list', methods=['GET'])
@limiter.limit("8 per minute")
@token_required
def get_risks(id_firm=None):
    """
    Route to get calculated risks (result of research).

    Method: GET.

    Args:
        - id_firm (int): Firm ID (passed via decorator @token_required)
        - dateFrom (str): Start date of the period. Default: '2024-08-01'
        - dateTo (str): Stop date of the period. Default: current date.

    Returns (List): List of calculated risks.
    """
    firm_id = id_firm
    logger.info('Receiving risk list for firm ID: %s', firm_id)
    # Get dateFrom and dateTo or set default
    dateFrom = request.args.get('dateFrom') or '2024-08-01'
    dateTo = request.args.get('dateTo') or datetime.now().strftime('%Y-%m-%d')

    try:
        # Transform string dateFrom to datetime, set format '%Y-%m-%d 00:00:00'
        dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')
    except ValueError:
        logger.warning('Get invalid dateFrom format from firm ID: %s', firm_id)
        return jsonify({'message': 'dateFrom must be in the format YYYY-MM-DD. Make sure month and day are valid values.'}), 400

    try:
        # Transform string dateTo to datetime, set format '%Y-%m-%d <current_time>'
        dateTo = datetime.strptime(f"{dateTo} {datetime.now().strftime('%H:%M:%S')}", '%Y-%m-%d %H:%M:%S')
    except ValueError:
        logger.warning('Get invalid dateTo format from firm ID: %s', firm_id)
        return jsonify({'message': 'dateTo must be in the format YYYY-MM-DD. Make sure month and day are valid values.'}), 400

    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
    try:
        with Session() as session:
            # Select all calculated risks for current firm_id between [dateFrom and dateTo]
            query = text(
                'SELECT r.name, r.birthday, t.type, r.risk, r.date '
                'FROM risks AS r '
                'LEFT JOIN type_risk AS t ON t.id = r.id_type '
                'WHERE r.id_firm = :firm_id AND r.date BETWEEN :dateFrom AND :dateTo'
            )
            result = session.execute(query, {'firm_id': firm_id, 'dateFrom': dateFrom, 'dateTo': dateTo})

            risk = [{
                     'name': row[0],
                     'birthday': row[1].strftime('%Y-%m-%d') if isinstance(row[1], (datetime, date)) else row[1],
                     'type': row[2],
                     'risk': float(row[3]),
                     'date': row[4].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[4], (datetime, date)) else row[4]} for row in result]
            logger.info('Successfully received %s risk lists for firm ID: %s', len(risk), firm_id)
            # Transform calculated risks info in JSON and return it
            response = make_response(json.dumps({'risk': risk}, ensure_ascii=False))
            response.headers['Content-Type'] = 'application/json; charset=utf-8'

            return response
    except Exception as e:
        logger.error("Error receiving risk list for firm ID %s: %s", firm_id, str(e))
        return jsonify({'error': "Internal server error"}), 500


@routes.route('/niimt/api/v1/calculate_risk', methods=['POST'])
@limiter.limit("1 per second")
@token_required
def risk_calculated(id_firm=None):
    """
    Route to send patients data.

    Method: POST.

    Args:
        - id_firm (int): Firm ID (passed via decorator @token_required)
        - user (str): Patient's full name
        - birthday (str): Patient's date of birth in format YYYY-mm-dd
        - snils (str): Patient's SNILS
        - gender (str): Patient's gender ('male' or 'female')
        - smoking (int): 1 for smoking patient, 0 for non-smoking patient
        - blood_pressure (int): Patient's blood_pressure level
        - cholesterol (float): Patient's cholesterol level
        - type (str): Type of calculated risk
        - return_answer (bool): True if calculated result should be returned. Default: False

    Data (list of dict): List of dictionaries containing patient data.
        Example:
        [{
         "user": "Иванов Иван Иванович",
         "birthday": "1968-09-25",
         "snils":  "74058576811",
         "gender": "male",
         "smoking": 1,
         "blood_pressure": 129,
         "cholesterol": 7.0,
         "type": "score",
         "return_answer": True
        }]

    Returns (List): List of calculated risks if return_answer == True else return message 'data for user snils {snils} has been sent successfully'
    """
    firm_id = id_firm

    result = []
    # Get data from user's query, check data types
    data = request.json
    logger.info('Request for risk calculation for %s patients from firm ID: %s', len(data), firm_id)
    for item in data:
        # Get risk name
        type_risk = item.get('type')
        if not isinstance(type_risk, str):
            logger.warning('Received unexpected type of risk from firm ID %s: %s', firm_id, type_risk)
            return jsonify({'message': f'The type of type_risk must be a string, not {type(type_risk).__name__}'}), 400
        if not type_risk in type_risks:
            logger.warning('Received invalid risk type from firm ID %s: %s', firm_id, type_risk)
            return jsonify({'message': 'This type of risk does not exist'}), 400

        # Create an instance of the class by risk type
        validator = type_risks[type_risk](item)
        # Check required fields
        is_valid = validator.validate()
        if not is_valid:
            logger.warning('Missing fields in query from firm ID: %s', firm_id)
            return jsonify({'message': 'Invalid request body'}), 400

        # Check count of received args
        is_count = validator.len_data_items()
        if not is_count:
            logger.warning('Too many arguments received from firm ID: %s', firm_id)
            return jsonify({'message': 'Too many arguments received'}), 400

        correct_types, res = validator.check_types(item)
        if not correct_types:
            logger.warning('Received arguments with unexpected types from firm ID: %s', firm_id)
            return res, 400

        # Check DB for presence of the current patient, in case of absence insert him into DB
        id_patient = check_patient(firm_id, **res)

        # Get risk ID (id_type) to pass it in function "add_research"
        # Create session to interact with DB
        Session = sessionmaker(bind=db.engine)
        try:
            with Session() as session:
                # Get risk ID by its name
                query = text('SELECT id FROM type_risk WHERE type = :type_risk')
                id_type = session.execute(query, {'type_risk': type_risk}).scalar()
                logger.info('Successfully received id_type from DB ')
        except Exception as e:
            logger.error("Error receiving id_type from DB: %s", str(e))
            return jsonify({'error': "Internal server error"}), 500

        # Add patient's info to DB (table 'research')
        try:
            validator.add_research(id_firm=firm_id, id_type=id_type, id_patient=id_patient, **res)
            logger.info("Patient's research data was added to DB successfully. Name: %s, snils: %s", res['user'], res['snils'])
        except Exception as e:
            logger.error("Failed to add patient's info to DB, patient_id: %s, kwargs: %s. Error: %s", id_patient, res, str(e))

        # Calculate risk for current patient
        try:
            risk = round(validator.calculate_risk(**res), 2)
            logger.info("Risk for id_patient: %s was calculated successfully", id_patient)
        except Exception as e:
            logger.error("Failed to calculate risk for id_patient %s, args: %s. Error: %s", id_patient, res, str(e))
            return jsonify({'error': 'Internal server error'}), 500

        # Add calculated risk to DB (table 'risks')
        add_risk(id_type, risk, firm_id, id_patient, **res)

        # Add to List 'result' calculated risk if return_answer == True, else add success message.
        # SNILS uses in messages to identify patient
        if res['return_answer']:
            result.append({'message': f'risk_score for user snils {res['snils']} = {risk}'})
        else:
            result.append({'message': f'data for user snils {res['snils']} has been sent successfully'})
    # Return result of the query to user
    logger.info("Data from %s patients was successfully proceeded and the result was sent to the user", len(result))
    return result