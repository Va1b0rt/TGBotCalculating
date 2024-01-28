from tables.Models import Employer


class NoSuitableEmployers(Exception):
    def __str__(self):
        return "Нет подходящих сотрудников."

    def __init__(self, employer: Employer):
        self.employer = employer
