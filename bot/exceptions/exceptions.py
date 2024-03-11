class GroupAlreadyExistsError(Exception):
    def __init__(self, group_name):
        self.group_name = group_name

    def __str__(self):
        return f'Группа "{self.group_name}" уже существует.'


class GroupNotFoundError(Exception):
    def __init__(self, group_name):
        self.group_name = group_name

    def __str__(self):
        return f'Группа "{self.group_name}" не существует.'


class GroupLimitExceededError(Exception):
    def __str__(self):
        return 'Превышено количество допустимых групп.'


class DataMissingError(Exception):
    def __str__(self):
        return 'Записи и группы отсутствуют.'
