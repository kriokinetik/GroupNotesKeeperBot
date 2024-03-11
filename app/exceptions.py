class GroupLimitExceededError(Exception):
    def __str__(self):
        return 'Превышено количество допустимых групп.'


class GroupAlreadyExistsError(Exception):
    def __str__(self):
        return 'Группа уже существует.'


class GroupNotFoundError(Exception):
    def __str__(self):
        return 'Группа не существует.'


class FileEmptyError(Exception):
    def __str__(self):
        return 'Записи и группы отсутствуют.'
