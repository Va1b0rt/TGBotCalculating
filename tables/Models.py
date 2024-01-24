import datetime

import pandas as pd
from pydantic import BaseModel
from tables import logger


class Worker(BaseModel):
    sex: str
    name: str
    job_title: str
    salary: str
    working_hours: str
    ident_IPN: str
    employment_date: str
    birthday: str
    dismissal: str

    @property
    def working_hours_coef(self):
        try:
            working_hours = int(self.working_hours)
            return working_hours / 8
        except ValueError as ex:
            logger.warning(ex)
            return None

    @property
    def salary_real(self):
        try:
            salary = float(self.salary)
            return round(salary * self.working_hours_coef)
        except (ValueError, TypeError) as ex:
            logger.warning(ex)
            return None

    @property
    def get_employment_date(self):
        try:
            date = datetime.datetime.strptime(self.employment_date, '%d.%m.%Y')
            return date
        except Exception as ex:
            logger.warning(ex)
            return None

    def salary_per_day(self, start_date: datetime.datetime, end_date) -> float:
        try:
            # Узнаем количество рабочих дней в месяце
            first_day_of_month = start_date.replace(day=1)
            last_day_of_month = (start_date + datetime.timedelta(days=35)).replace(day=1) - datetime.timedelta(days=1)
            working_days_per_month = self.count_working_days(first_day_of_month, last_day_of_month)

            # Узнаем сколько стоит рабочий день
            salary_per_day = float(self.salary) / working_days_per_month

            return round(salary_per_day, 2)

        except Exception as ex:
            logger.warning(ex)
            return 0.0

    def salary_for_period(self, start_date: datetime.datetime, end_date) -> float:
        try:
            salary_per_day = self.salary_per_day(start_date, end_date)

            # Узнаем зп за нужный период
            days_for_current_period = self.count_working_days(start_date, end_date)
            salary_for_current_period = salary_per_day * days_for_current_period

            return round(salary_for_current_period)

        except Exception as ex:
            logger.warning(ex)
            return 0.0

    @staticmethod
    def count_working_days(start_date, end_date) -> int:
        # Создаем диапазон дат с использованием библиотеки pandas
        date_range = pd.date_range(start=start_date, end=end_date)

        # Фильтруем только рабочие дни (понедельник - пятница)
        working_days = date_range[date_range.weekday < 5]

        # Возвращаем количество рабочих дней
        return len(working_days)

    def if_employment_later_last_month(self):
        today = datetime.date.today()
        first_day_of_this_month = today.replace(day=1)
        last_day_of_last_month = first_day_of_this_month - datetime.timedelta(days=1)
        previous_month = last_day_of_last_month.month

        if int(self.employment_date.split('.')[1]) > previous_month:
            return True

        if self.dismissal != '':
            if int(self.dismissal.split('.')[1]) < previous_month:
                return True

        return False


class Employer(BaseModel):
    name: str
    ident_EDRPOU: str
    workers: list[Worker]
    residence: str
    phone: str


if __name__ == '__main__':
    worker1 = Worker(
        sex="Male",
        name="John Doe",
        job_title="Software Engineer",
        salary="5000",
        working_hours="8",
        ident_IPN="1234567890",
        employment_date='01.11.2023',
        birthday='01.01.1990',
        dismissal=''
    )

    worker2 = Worker(
        sex="Female",
        name="Jane Smith",
        job_title="Data Scientist",
        salary="6000",
        working_hours="8",
        ident_IPN="0987654321",
        employment_date='01.11.2023',
        birthday='01.01.1990',
        dismissal=''
    )

    # Создание объекта Employer с несколькими работниками
    employer = Employer(
        name="Acme Corporation",
        ident_EDRPOU="123456789",
        workers=[worker1, worker2],
        residence='qwee',
        phome='12312312'
    )

    print(employer.model_dump_json())
