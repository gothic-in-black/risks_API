import math
from flask import jsonify
from datetime import datetime


class BaseValidator:
    """
    Basic validator to check if data contains required fields.

    The class is created to check that all required fields are presented in transmitted data.

    Attributes:
        - required_fields (list): List of the required fields.
        - data (dict): Data for checking.

    Methods:
        - validate(): Checks whether all required fields are present in data.
        - len_data_items(): Checks that the number of arguments received from user matches the expected number of arguments.
        - check_types(): Checks types of the base arguments received from user.
    """
    required_fields = []
    correct_len = 0

    def __init__(self, data):
        """
        Initializes a validator object with the data to be validated.

        Args:
            - data (dict): Data for checking.
        """
        self.data = data

    def validate(self):
        """
        Checks whether all required fields are present in data.

        Returns (bool): True if all required fields are present in data, else False
        """
        missing_fields = [field for field in self.required_fields if field not in self.data]
        if missing_fields:
            return False
        return True

    def len_data_items(self):
        """
        Checks that the number of arguments received from user matches the expected number of arguments.

        Returns (bool): True if number of arguments in user data matches the expected number of arguments, else False
        """
        if len(self.data) > self.correct_len:
            return False
        return True

    def check_types(self, item):
        """
        Checks the types of data received from user, that are independent of the risk type.

        Args:
            - item (dict): Data for checking.

        Returns (tuple):
            - bool: True if all checks were successful else False.
            - dict or Response: returns dict with valid data if all checks were successful else returns Response object with the error message.
        """
        user = item.get('user')
        if not isinstance(user, str):
            return False, jsonify({'message': f'The type of user must be a string, not a {type(user).__name__}.'})

        birthday_date = item.get('birthday')
        if not isinstance(birthday_date, str):
            return False, jsonify({'message': f'The type of birthday must be a string, not a {type(birthday_date).__name__}.'})
        try:
            birthday = datetime.strptime(birthday_date, '%Y-%m-%d').date()
        except ValueError:
            return False, jsonify({'message': 'The birthday must be in the format YYYY-MM-DD.'})

        snils = item.get('snils')
        if not isinstance(snils, int):
            return False, jsonify({'message': f'The type of snils must be an int, not {type(snils).__name__}'})

        gender = item.get('gender')
        if not isinstance(gender, str):
            return False, jsonify({'message': f'The type of gender must be a string, not {type(gender).__name__}'})
        if not gender in ['male', 'female']:
            return False, jsonify({'message': 'The gender must be a male or female'})

        return_answer = item.get('return_answer', False)
        if not isinstance(return_answer, bool):
            return False, jsonify({'message': f'The type of return_answer must be a bool, not {type(return_answer).__name__}'})

        return True, {'user': user, 'birthday': birthday, 'snils': snils, 'gender': gender, 'return_answer': return_answer}



class ScoreRiskValidator(BaseValidator):
    """
    Validator for SCORE risk calculation.

    This class extends the capabilities of the base validator by adding specific fields for risk calculation.
    After successful validation, performs risk calculation based on the provided data.

    Attributes:
        - required_fields (list): List of the required fields for risk calculation.
        - data (dict): Data for checking and using in risk calculation.

    Methods:
        - calculate_risk(age, gender, is_smoker, systolic_bp, cholesterol):
            Calculate risk based on medical tests such as: age, gender, smoking, blood pressure and cholesterol level.\
        - check_types(): Checks types of the arguments received from user, that are needed for score risk calculation.
    """
    required_fields = ['user', 'birthday', 'snils', 'gender', 'smoking', 'blood_pressure', 'cholesterol', 'type']
    correct_len = 9

    def calculate_risk(self, birthday, gender, smoking, blood_pressure, cholesterol, **kwargs):
        """
        Calculates risk based on given parameters.

        Args:
            - birthday (str): Patient's date of birth.
            - gender (str): Patient gender ('male' or 'female').
            - smoking (int): 1 for smoking patient, 0 for non-smoking patient.
            - blood_pressure (int): Blood pressure of the patient.
            - cholesterol (float): Cholesterol level of the patient.

        Returns (float): Calculated risk.
        """
        # Calculate patient's age for current moment
        age = datetime.now().year - birthday.year - ((datetime.now().month, datetime.now().day) < (birthday.month, birthday.day))
        # Set coefficients and constants depending on gender
        if gender.lower() == 'male':
            alpha = -21.0
            p = 4.62
            alpha2 = -25.7
            p2 = 5.47
        else:  # for female
            alpha = -28.7
            p = 6.23
            alpha2 = -30.0
            p2 = 6.42

        # Calculate cs0 and cs10
        cs0 = math.exp(-math.exp(alpha) * ((age - 20) ** p))
        cs10 = math.exp(-math.exp(alpha) * ((age - 10) ** p))

        # Calculate ncs0 and ncs10
        ncs0 = math.exp(-math.exp(alpha2) * ((age - 20) ** p2))
        ncs10 = math.exp(-math.exp(alpha2) * ((age - 10) ** p2))

        # Coefficients for smoking patients
        bsm = 0.71 if smoking else 0

        # Calculate wc for cs
        wc = 0.24 * (cholesterol - 6.0) + 0.018 * (blood_pressure - 120) + bsm

        # Coefficients for smoking patients
        bsm = 0.63 if smoking else 0

        # Calculate wnc for ncs
        wnc = 0.02 * (cholesterol - 6.0) + 0.022 * (blood_pressure - 120) + bsm

        # Calculate cs1 and ncs1
        cs = cs0 ** math.exp(wc)
        cs1 = cs10 ** math.exp(wc) / cs
        ncs = ncs0 ** math.exp(wnc)
        ncs1 = ncs10 ** math.exp(wnc) / ncs

        # Result risk
        r = 1.0 - cs1
        r1 = 1.0 - ncs1

        # Return the result as a percentage
        return round(100.0 * (r + r1), 2)

    def check_types(self, item):
        """
        Checks the types of data received from user, that are needed for score risk calculation.

        Args:
            - item (dict): Data for checking.

        Returns (tuple):
            - bool: True if all checks were successful else False.
            - dict or Response: returns dict with valid data if all checks were successful else returns Response object with the error message.
        """
        is_valid, result = super().check_types(item)
        if not is_valid:
            return False, result

        # smoking: 1 - yes, 0 - no
        smoking = item.get('smoking')
        if not isinstance(smoking, int):
            return False, jsonify({'message': f'The type of smoking must be an integer, not a {type(smoking).__name__}'})
        if not smoking in [0, 1]:
            return False, jsonify({'message': 'The smoking must be a 0 or 1'})

        blood_pressure = item.get('blood_pressure')
        if not isinstance(blood_pressure, int):
            return False, jsonify({'message': f'The type of blood_pressure must be an integer, not {type(blood_pressure).__name__}'})

        cholesterol = item.get('cholesterol')
        if not isinstance(cholesterol, float):
            return False, jsonify({'message': f'The type of cholesterol must be a float, not {type(cholesterol).__name__}'})

        valid_data = {**result.copy(), **{'smoking': smoking, 'blood_pressure': blood_pressure, 'cholesterol': cholesterol}}

        return True, valid_data


# This dict is used in "routes.py" to create an instance of the right class accordingly user query.
# Key of the dict is received from user data, Value is name of the corresponding class
type_risks = {
    'score': ScoreRiskValidator
}