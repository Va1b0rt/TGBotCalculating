class NotExistsFourDF(Exception):
    def __str__(self):
        return "Не нашёл 4ДФ с указанными параметрами"


class UserWasExists(Exception):
    def __str__(self):
        return "Указанный пользователь уже существует"


class UserNotExists(Exception):
    def __str__(self):
        return "Указанный пользователь не существует"
