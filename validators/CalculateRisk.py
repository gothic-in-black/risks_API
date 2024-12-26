import math


class BaseValidator:
    """
    Basic validator to check if data contains required fields.

    The class is created to check that all required fields are presented in transmitted data.

    Attributes:
        - required_fields (list): List of the required fields.
        - data (dict): Data for checking.

    Methods:
        validate(): Checks whether all required fields are present in data.
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


class ScoreRiskValidator(BaseValidator):
    """
    Validator for SCORE risk calculation.

    This class extends the capabilities of the base validator by adding specific fields for risk calculation.
    After successful validation, performs risk calculation based on the provided data.

    Attributes:
        - required_fields (list): List of the required fields for risk calculation.
        - data (dict): Data for checking and using in risk calculation.

    Methods:
        calculate_risk(age, gender, is_smoker, systolic_bp, cholesterol):
            Calculate risk based on medical tests such as: age, gender, smoking, blood pressure and cholesterol level.
    """
    required_fields = ['user', 'birthday', 'snils', 'gender', 'smoking', 'blood_pressure', 'cholesterol', 'type']
    correct_len = 9

    def calculate_risk(self, age, gender, is_smoker, systolic_bp, cholesterol):
        """
        Calculates risk based on given parameters.

        Args:
            - age (int): Patient age.
            - gender (str): Patient gender ('male' or 'female').
            - is_smoker (bool): True for smoking patient, False for non-smoking.
            - systolic_bp (int): Blood pressure of the patient.
            - cholesterol (int): Cholesterol level of the patient.

        Returns (float): Calculated risk.
        """
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


# This dict is used in "routes.py" to create an instance of the right class accordingly user query
# Key of the dict is received from user data, Value is name of the corresponding class
type_risks = {
    'score': ScoreRiskValidator
}