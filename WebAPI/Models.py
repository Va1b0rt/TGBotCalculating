from pydantic import BaseModel


class Worker(BaseModel):
    id: int
    sex: str
    name: str
    job_title: str
    salary: str
    working_hours: str
    ident_IPN: str
    employment_date: str
    birthday: str
    dismissal: str


class Employer(BaseModel):
    id: int
    name: str
    ident_EDRPOU: str
    workers: list[Worker]
    residence: str
    phone: str


class Response(BaseModel):
    data: list[Employer]
    content_range: str
