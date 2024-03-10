import json

from fastapi import Query, Path, Body, HTTPException, Response
from typing import List, Optional, Any

from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from DBAPI.DBClient import DBClient
from .Models import Employer

from . import app


@app.get("/employers", response_model=List[Employer])
async def get_employers(
    _sort: Optional[str] = Query(None),
    _range: Optional[str] = Query(None),
    _filter: Optional[str] = Query(None)
):
    # Получаем все записи из таблицы Employer
    filter_dict: Optional[dict] = None
    sort_list: Optional[list] = None
    range_list: Optional[list] = None

    if _filter:
        try:
            filter_dict = json.loads(_filter)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid filter JSON data")

    if _sort:
        try:
            sort_list = json.loads(_sort)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid sort JSON data")

    if _range:
        try:
            range_list = json.loads(_range)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid range JSON data")

    query, total = DBClient().get_employers(_filter=filter_dict,
                                            _sort=sort_list,
                                            _range=range_list)

    employers = [model_to_dict(employer, recurse=True, backrefs=True) for employer in query]

    response = Response(content=json.dumps(employers))

    content_range = f"0-{len(employers) - 1}/{total}"

    response.headers["content-range"] = content_range

    return response


# Get a single employer by id
@app.get("/employer/{employer_id}", response_model=Employer)
async def get_employer(employer_id: int = Path(...)):
    try:
        employer = DBClient().get_employer(employer_id=employer_id)
    except DoesNotExist:
        # Если записи нет, возвращаем ошибку 404
        raise HTTPException(status_code=404, detail="Employer not found")
    # Преобразуем результат в словарь
    #employer = model_to_dict(employer)
    return employer


# Get multiple employers by ids
@app.get("/employer/multiple", response_model=List[Employer])
async def get_multiple_employers(filter: dict = Body(...)):
    if "id" in filter and isinstance(filter["id"], list):
        ids = filter["id"]
        # Получаем все записи из таблицы Employer, у которых id в списке ids
        query = Employer.select().where(Employer.id.in_(ids))
        # Преобразуем результат в список словарей
        employers = [model_to_dict(employer) for employer in query]
        return employers
    raise HTTPException(status_code=400, detail="Invalid filter")


# Create an employer
@app.post("/employer", response_model=Employer)
async def create_employer(employer: Employer = Body(...)):
    # Создаем новую запись в таблице Employer с данными из тела запроса
    employer = Employer.create(**employer.dict())
    # Преобразуем результат в словарь
    employer = model_to_dict(employer)
    return employer


# Update an employer by id
@app.put("/employer/{id}", response_model=Employer)
async def update_employer(id: int = Path(...), employer: Employer = Body(...)):
    # Ищем запись по id в таблице Employer
    try:
        old_employer = Employer.get_by_id(id)
    except DoesNotExist:
        # Если записи нет, возвращаем ошибку 404
        raise HTTPException(status_code=404, detail="Employer not found")
    # Обновляем запись с данными из тела запроса
    old_employer.update(**employer.dict()).execute()
    # Преобразуем результат в словарь
    employer = model_to_dict(old_employer)
    return employer


# Update multiple employers by ids
@app.put("/employer/multiple", response_model=List[Employer])
async def update_multiple_employers(filter: dict = Body(...), employer: Employer = Body(...)):
    if "id" in filter and isinstance(filter["id"], list):
        ids = filter["id"]
        # Получаем все записи из таблицы Employer, у которых id в списке ids
        query = Employer.select().where(Employer.id.in_(ids))
        # Обновляем все записи с данными из тела запроса
        query.update(**employer.dict()).execute()
        # Преобразуем результат в список словарей
        employers = [model_to_dict(employer) for employer in query]
        return employers
    raise HTTPException(status_code=400, detail="Invalid filter")


# Delete an employer by id
@app.delete("/employer/{id}")
async def delete_employer(id: int = Path(...)):
    # Ищем запись по id в таблице Employer
    try:
        employer = Employer.get_by_id(id)
    except DoesNotExist:
        # Если записи нет, возвращаем ошибку 404
        raise HTTPException(status_code=404, detail="Employer not found")
    # Удаляем запись из таблицы
    employer.delete_instance()
    return {"message": "Employer deleted"}


# Delete multiple employers by ids
@app.delete("/employer/multiple")
async def delete_multiple_employers(filter: dict = Body(...)):
    # Check if the filter has a key "id" with a list of ids
    # Проверяем, есть ли в фильтре ключ "id" со списком id
    if "id" in filter and isinstance(filter["id"], list):
        ids = filter["id"]
        # Ищем и удаляем предпринимателей с данными id
        result = []
        for id in ids:
            try:
                # Находим запись по id в таблице Employer
                employer = Employer.get_by_id(id)
                # Удаляем запись из таблицы
                employer.delete_instance()
                # Добавляем запись в результат
                result.append(model_to_dict(employer))
            except DoesNotExist:
                # Если записи нет, пропускаем ее
                pass
        return {"message": "Employers deleted", "data": result}
    # Если нет, возвращаем ошибку
    raise HTTPException(status_code=400, detail="Invalid filter")

