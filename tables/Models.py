from pydantic import BaseModel


class Worker(BaseModel):
    sex: str
    name: str
    job_title: str
    salary: str
    working_hours: str
    ident_IPN: str
    employment_date: str


class Employer(BaseModel):
    name: str
    ident_EDRPOU: str
    workers: list[Worker]


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
