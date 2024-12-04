import math
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from . import db


def calculate_score_risk(age, gender, is_smoker, systolic_bp, cholesterol):
    # Устанавливаем коэффициенты и константы в зависимости от пола
    if gender.lower() == 'male':
        alpha = -21.0
        p = 4.62
        alpha2 = -25.7
        p2 = 5.47
    else:  # для женщин
        alpha = -28.7
        p = 6.23
        alpha2 = -30.0
        p2 = 6.42

    # Расчет cs0 и cs10
    cs0 = math.exp(-math.exp(alpha) * ((age - 20) ** p))
    cs10 = math.exp(-math.exp(alpha) * ((age - 10) ** p))

    # Расчет ncs0 и ncs10
    ncs0 = math.exp(-math.exp(alpha2) * ((age - 20) ** p2))
    ncs10 = math.exp(-math.exp(alpha2) * ((age - 10) ** p2))

    # Коэффициенты для курящих
    bsm = 0.71 if is_smoker else 0

    # Расчет wc для cs
    wc = 0.24 * (cholesterol - 6.0) + 0.018 * (systolic_bp - 120) + bsm

    # Коэффициенты для курящих
    bsm = 0.63 if is_smoker else 0

    # Расчет wnc для ncs
    wnc = 0.02 * (cholesterol - 6.0) + 0.022 * (systolic_bp - 120) + bsm

    # Расчет cs1 и ncs1
    cs = cs0 ** math.exp(wc)
    cs1 = cs10 ** math.exp(wc) / cs
    ncs = ncs0 ** math.exp(wnc)
    ncs1 = ncs10 ** math.exp(wnc) / ncs

    # Итоговый риск
    r = 1.0 - cs1
    r1 = 1.0 - ncs1

    # Возвращаем результат в процентах
    return round(100.0 * (r + r1), 2)


def check_patient(snils, id_firm, user, birthday, gender):
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        query = text('SELECT count(snils) FROM patients WHERE snils = :snils AND id_firm = :id_firm')  # :snils это переменная

        result = session.execute(query, {'snils': snils, 'id_firm': id_firm}).scalar()

        if result == 0:
            #создаем запись в таблице БД
            query = text('INSERT INTO patients (name, birthday, gender, snils, id_firm) VALUES (:name, :birthday, :gender, :snils, :id_firm)')

            session.execute(query, {'name': user, 'birthday': birthday, 'gender': gender, 'snils': snils, 'id_firm': id_firm})
            session.commit()

        query_id_patience = text('SELECT id FROM patients WHERE snils = :snils AND id_firm = :id_firm')
        id_patience = session.execute(query_id_patience, {'snils': snils, 'id_firm': id_firm}).scalar()
        return id_patience


def add_research(id_type, patient_id, name, birthday, gender, cholesterol, ad, smoking, firm_id):
    date_research = (datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        query = text('INSERT INTO research (id_type, date, id_patient, name, birthday, gender, cholesterol, ad, smoking, id_firm) '
                     'VALUES (:id_type, :date_research, :patient_id, :name, :birthday, :gender, :cholesterol, :ad, :smoking, :firm_id)')
        session.execute(query, {'id_type': id_type, 'date_research': date_research, 'patient_id': patient_id, 'name': name, 'birthday': birthday,
                                'gender': gender, 'cholesterol': cholesterol, 'ad': ad, 'smoking': smoking, 'firm_id': firm_id})
        session.commit()


def add_risk(id_type, risk, id_patient, name, birthday, id_firm):
    date_calculate = (datetime.now()).strftime('%Y-%m-%d %H:%M:%S')
    Session = sessionmaker(bind=db.engine)
    with Session() as session:
        query = text('INSERT INTO risks (id_type, risk, id_patient, name, birthday, id_firm, date) VALUES (:id_type, :risk, :id_patient, :name, :birthday, :id_firm, :date_calculate)')
        session.execute(query, {'id_type': id_type, 'risk': risk, 'id_patient': id_patient, 'name': name, 'birthday': birthday, 'id_firm': id_firm, 'date_calculate': date_calculate})
        session.commit()