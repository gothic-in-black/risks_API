import json
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from flask import make_response
from datetime import datetime, date

from . import db
from .auth import token_required
from .utils import check_patient, add_risk
from validators.CalculateRisk import type_risks


# Create a Blueprint instance named 'routes'
routes = Blueprint('routes', __name__)

# Route registration
@routes.route('/niimt/api/v1/patients_list', methods=['GET'])
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
    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        # Select all employees of the firm with current firm_id
        query = text('SELECT name, snils FROM patients WHERE id_firm = :firm_id')
        result = session.execute(query, {'firm_id': firm_id})
        patients = [{'name': row[0], 'snils': row[1]} for row in result]

        # Transform patients info in JSON and return it
        response = make_response(json.dumps({'patients': patients}, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        return response


@routes.route('/niimt/api/v1/research_list', methods=['GET'])
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
    # Get dateFrom and dateTo or set default
    dateFrom = request.args.get('dateFrom') or '2024-08-01'
    dateTo = request.args.get('dateTo') or datetime.now().strftime('%Y-%m-%d')

    # Transform string dateFrom to datetime, set format '%Y-%m-%d 00:00:00'
    dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')

    # Transform string dateTo to datetime, set format '%Y-%m-%d <current_time>'
    dateTo = datetime.strptime(f'{dateTo} {datetime.now().strftime('%H:%M:%S')}', '%Y-%m-%d %H:%M:%S')

    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        # Select all research for current firm_id between [dateFrom and dateTo]
        query = text('SELECT date, name, birthday, gender, cholesterol, ad, smoking '
                     'FROM research WHERE id_firm = :firm_id AND date BETWEEN :dateFrom AND :dateTo')
        result = session.execute(query, {'firm_id': firm_id, 'dateFrom': dateFrom, 'dateTo': dateTo})

        research = [{'date': row[0].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[0], (datetime, date)) else row[0],
                     'name': row[1],
                     'birthday': row[2].strftime('%Y-%m-%d') if isinstance(row[2], (datetime, date)) else row[2],
                     'gender': row[3],
                     'cholesterol': float(row[4]),
                     'ad': row[5],
                     'smoking': row[6]} for row in result]

        # Transform research info in JSON and return it
        response = make_response(json.dumps({'research': research}, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        return response


@routes.route('/niimt/api/v1/risk_list', methods=['GET'])
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
    # Get dateFrom and dateTo or set default
    dateFrom = request.args.get('dateFrom') or '2024-08-01'
    dateTo = request.args.get('dateTo') or datetime.now().strftime('%Y-%m-%d')

    # Transform string dateFrom to datetime, set format '%Y-%m-%d 00:00:00'
    dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')

    # Transform string dateTo to datetime, set format '%Y-%m-%d <current_time>'
    dateTo = datetime.strptime(f'{dateTo} {datetime.now().strftime('%H:%M:%S')}', '%Y-%m-%d %H:%M:%S')

    # Create session to interact with DB
    Session = sessionmaker(bind=db.engine)
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

        # Transform calculated risks info in JSON and return it
        response = make_response(json.dumps({'risk': risk}, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        return response


@routes.route('/niimt/api/v1/calculate_risk', methods=['POST'])
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
    result = []
    # Get data from user's query, check data types
    data = request.json

    for item in data:
        # Get risk name
        type_risk = item.get('type')
        if not isinstance(type_risk, str):
            return jsonify({'message': f'The type of type_risk must be a string, not {type(type_risk).__name__}'}), 400
        if not type_risk in type_risks:
            return jsonify({'message': 'This type of risk does not exist'}), 400

        # Create an instance of the class by risk type
        validator = type_risks[type_risk](item)
        # Check required fields
        is_valid = validator.validate()
        if not is_valid:
            return jsonify({'message': 'Invalid request body'}), 400

        # Check count of received args
        is_count = validator.len_data_items()
        if not is_count:
            return jsonify({'message': 'Too many arguments received'}), 400

        firm_id = id_firm

        correct_types, res = validator.check_types(item)
        if not correct_types:
            return res, 400

        # Check DB for presence of the current patient, in case of absence insert him into DB
        id_patient = check_patient(firm_id, **res)

        # Get risk ID (id_type) to pass it in function "add_research"
        # Create session to interact with DB
        Session = sessionmaker(bind=db.engine)
        with Session() as session:
            # Get risk ID by its name
            query = text('SELECT id FROM type_risk WHERE type = :type_risk')
            id_type = session.execute(query, {'type_risk': type_risk}).scalar()

        # Add patient's info in DB (table 'research')
        validator.add_research(id_firm=firm_id, id_type=id_type, id_patient=id_patient, **res)

        # Calculate risk for current patient
        risk = validator.calculate_risk(**res)

        # Add calculated risk in DB (table 'risks')
        add_risk(id_type, risk, firm_id, id_patient, **res)

        # Add to List 'result' calculated risk if return_answer == True, else add success message.
        # SNILS uses in messages to identify patient
        if res['return_answer']:
            result.append({'message': f'risk_score for user snils {res['snils']} = {risk}'})
        else:
            result.append({'message': f'data for user snils {res['snils']} has been sent successfully'})
    # Return result of the query to user
    return result