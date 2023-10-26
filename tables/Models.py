import datetime

from pydantic import BaseModel


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
        ident_IPN="1234567890"
    )

    worker2 = Worker(
        sex="Female",
        name="Jane Smith",
        job_title="Data Scientist",
        salary="6000",
        working_hours="8",
        ident_IPN="0987654321"
    )

    # Создание объекта Employer с несколькими работниками
    employer = Employer(
        name="Acme Corporation",
        ident_EDRPOU="123456789",
        workers=[worker1, worker2]
    )

    print(employer.model_dump_json())
