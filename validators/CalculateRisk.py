# в этом классе проверяется, все ли показатели для расчета риска переданы
# сейчас у меня только один риск
# Если добавятся новые, то:
#                           - переименовать классы (названия рисков)
#                           - в POST запросе сейчас проверяются показатели только для первого риска (row 329 в main_full.py). Надо переписать логику


class CalculateRiskValidator:
    required_fields = ['user', 'birthday', 'snils', 'gender', 'smoking', 'blood_pressure', 'cholesterol', 'type']

    def __init__(self, data):
        self.data = data

    def validate(self):
        missing_fields = [field for field in self.required_fields if field not in self.data]
        if missing_fields:
            return False
        return True

