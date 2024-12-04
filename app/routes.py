import json
from flask import Blueprint, request, jsonify
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from flask import make_response
from datetime import datetime, date


from . import db
from .auth import token_required
from .utils import calculate_score_risk, check_patient, add_research, add_risk
from validators.CalculateRisk import CalculateRiskValidator




routes = Blueprint('routes', __name__)

@routes.route('/niimt/api/v1/patients_list', methods=['GET'])
@token_required
def get_listOfEmployees(id_firm=None):
    firm_id = id_firm
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        query = text('SELECT name, snils FROM patients WHERE id_firm = :firm_id')
        result = session.execute(query, {'firm_id': firm_id})
        session.commit()
        patients = [{'name': row[0], 'snils': row[1]} for row in result]

        response = make_response(json.dumps({'patients': patients}, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        return response



@routes.route('/niimt/api/v1/research_list', methods=['GET'])
@token_required
def get_research(id_firm=None):
    firm_id = id_firm
    dateFrom = request.args.get('dateFrom') or '2024-08-01'
    dateTo = request.args.get('dateTo') or datetime.now().strftime('%Y-%m-%d')

    # Преобразуем dateFrom в datetime и добавляем время 00:00:00
    dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')

    # Преобразуем dateTo в datetime и добавляем время 23:59:59, если не указано
    if ' ' not in dateTo:
        dateTo = datetime.strptime(dateTo, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')

    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        query = text('SELECT date, name, birthday, gender, cholesterol, ad, smoking '
                     'FROM research WHERE id_firm = :firm_id AND date BETWEEN :dateFrom AND :dateTo')
        result = session.execute(query, {'firm_id': firm_id, 'dateFrom': dateFrom, 'dateTo': dateTo})

        # Convert the result to a JSON-compatible format, ensuring dates are strings
        research = [{'date': row[0].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[0], (datetime, date)) else row[0],
                     'name': row[1],
                     'birthday': row[2].strftime('%Y-%m-%d') if isinstance(row[2], (datetime, date)) else row[2],
                     'gender': row[3],
                     'cholesterol': float(row[4]),
                     'ad': row[5],
                     'smoking': row[6]} for row in result]

        response = make_response(json.dumps({'research': research}, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        return response


@routes.route('/niimt/api/v1/risk_list', methods=['GET'])
@token_required
def get_risks(id_firm=None):
    firm_id = id_firm
    dateFrom = request.args.get('dateFrom') or '2024-08-01'
    dateTo = request.args.get('dateTo') or datetime.now().strftime('%Y-%m-%d')

    # Преобразуем dateFrom в datetime и добавляем время 00:00:00
    dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').strftime('%Y-%m-%d 00:00:00')

    # Преобразуем dateTo в datetime и добавляем время 23:59:59, если не указано
    if ' ' not in dateTo:
        dateTo = datetime.strptime(dateTo, '%Y-%m-%d').strftime('%Y-%m-%d 23:59:59')

    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        query = text(
            'SELECT name, '
            'birthday, '
            'CASE WHEN id_type = 1 THEN \'score\' '
            'ELSE \'no name\' '
            'END AS type, '
            'risk, '
            'date '
            'FROM risks WHERE id_firm = :firm_id AND date BETWEEN :dateFrom AND :dateTo'
        )
        result = session.execute(query, {'firm_id': firm_id, 'dateFrom': dateFrom, 'dateTo': dateTo})

        risk = [{
                 'name': row[0],
                 'birthday': row[1].strftime('%Y-%m-%d') if isinstance(row[1], (datetime, date)) else row[1],
                 'type': row[2],
                 'risk': float(row[3]),
                 'date': row[4].strftime('%Y-%m-%d %H:%M:%S') if isinstance(row[4], (datetime, date)) else row[4]} for row in result]
        response = make_response(json.dumps({'risk': risk}, ensure_ascii=False))
        response.headers['Content-Type'] = 'application/json; charset=utf-8'

        return response


@routes.route('/niimt/api/v1/calculate_risk', methods=['POST'])
@token_required
def post(id_firm=None):

    result = []

    data = request.json
    for item in data:
        validator = CalculateRiskValidator(item)
        is_valid = validator.validate()
        if not is_valid:
            return jsonify({'message': 'Invalid request body'}), 400

        user = item.get('user')
        if not isinstance(user, str):
            return jsonify({'message': f'The type of user must be a string, not a {type(user).__name__}.'}), 403

        birthday_date = item.get('birthday')
        if not isinstance(birthday_date, str):
            return jsonify({'message': f'The type of birthday must be a string, not a {type(birthday_date).__name__}.'}), 403
        try:
            birthday = datetime.strptime(birthday_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'message': 'The birthday must be in the format YYYY-MM-DD.'}), 403

        age = datetime.now().year - birthday.year - ((datetime.now().month, datetime.now().day) < (birthday.month, birthday.day))
        snils = int(item.get('snils'))
        if not isinstance(snils, int):
            return jsonify({'message': f'The type of shils must be a int, not {type(snils).__name__}'})

        gender = item.get('gender')
        if not isinstance(gender, str):
            return jsonify({'message': f'The type of gender must be a string, not {type(gender).__name__}'})
        if not gender in ['male', 'female']:
            return jsonify({'message': 'The gender must be a male or female'})

        smoking = item.get('smoking') #передается число 1(да) или 0(нет)
        if not isinstance(smoking, int):
            return jsonify({'message': f'The type of smoking must be a integer, not a {type(smoking).__name__}'})
        if not smoking in [0, 1]:
            return jsonify({'message': 'The smoking must be a 0 or 1'})

        blood_pressure = item.get('blood_pressure')
        if not isinstance(blood_pressure, int):
            return jsonify({'message': f'The type of blood_pressure must be an integer, not {type(blood_pressure).__name__}'})
        cholesterol = item.get('cholesterol')
        if not isinstance(cholesterol, float):
            return jsonify({'message': f'The type of cholesterol must be a float, not {type(cholesterol).__name__}'})

        type_risk = item.get('type')
        if not isinstance(type_risk, str):
            return jsonify({'message': f'The type of type_risk must be a string, not {type(type_risk).__name__}'})
        if not type_risk in ['score']:
            return jsonify({'message': 'This type of risk does not exist'})

        return_answer = item.get('return_answer') or False  # return по умолчанию равен False
        if not isinstance(return_answer, bool):
            return jsonify({'message': f'The type of return_answer must be a bool, not {type(return_answer).__name__}'})

        # сохраняем в переменную id фирмы
        firm_id = id_firm

        #проверяем пациента на наличие в таблице patients
        #сохраняем в переменную id пациента
        id_patient = check_patient(snils, firm_id, user, birthday, gender)


        #сохраняем в переменную id_type
        Session = sessionmaker(bind=db.engine)
        with Session() as session:
            query = text('SELECT id FROM type_risk WHERE type = :type_risk')
            id_type = session.execute(query, {'type_risk': type_risk}).scalar()
            session.commit()


        #добавляем запись в таблицу research
        add_research(id_type, id_patient, user, birthday_date, gender, cholesterol, blood_pressure, smoking, firm_id)

        #рассчитываем риск (score)
        if id_type == 1:
            risk = calculate_score_risk(age, gender, smoking, blood_pressure, cholesterol)

        #добавляем запись в таблицу risk
        add_risk(id_type, risk, id_patient, user, birthday_date, firm_id)

        #возвращаем (по требованию) результат рассчета риска
        if return_answer:
            result.append({'message': f'risk_score for user snils {snils} = {risk}'})
        else:
            result.append({'message': f'data for user snils {snils} has been sent successfully'})

    return result