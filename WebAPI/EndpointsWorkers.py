from typing import List, Optional

from fastapi import HTTPException
from fastapi.params import Query, Path, Body
from peewee import DoesNotExist
from playhouse.shortcuts import model_to_dict

from .Models import Worker

from . import app


@app.get("/worker", response_model=List[Worker])
async def get_workers(
    sort: Optional[List[str]] = Query(None),
    range: Optional[List[int]] = Query(None),
    filter: Optional[dict] = Body(None)
):
    # Получаем все записи из таблицы Worker
    query = Worker.select()
    # Применяем фильтры, если они есть
    if filter:
        for key, value in filter.items():
            # Используем оператор LIKE для поиска по подстроке
            query = query.where(getattr(Worker, key).contains(value))
    # Применяем сортировку, если она есть
    if sort:
        for field in sort:
            # Определяем порядок сортировки по знаку + или -
            if field.startswith("-"):
                query = query.order_by(getattr(Worker, field[1:]).desc())
            else:
                query = query.order_by(getattr(Worker, field))
    # Применяем диапазон, если он есть
    if range:
        start, end = range
        query = query.limit(end - start + 1).offset(start)
    # Преобразуем результат в список словарей
    workers = [model_to_dict(worker) for worker in query]
    return workers


# Создаем конечную точку для получения одного работника по id
@app.get("/worker/{id}", response_model=Worker)
async def get_worker(id: int = Path(...)):
    # Ищем запись по id в таблице Worker
    try:
        worker = Worker.get_by_id(id)
    except DoesNotExist:
        # Если записи нет, возвращаем ошибку 404
        raise HTTPException(status_code=404, detail="Worker not found")
    # Преобразуем результат в словарь
    worker = model_to_dict(worker)
    return worker


# Создаем конечную точку для получения нескольких работников по списку id
@app.get("/worker/multiple", response_model=List[Worker])
async def get_multiple_workers(filter: dict = Body(...)):
    if "id" in filter and isinstance(filter["id"], list):
        ids = filter["id"]
        # Получаем все записи из таблицы Worker, у которых id в списке ids
        query = Worker.select().where(Worker.id.in_(ids))
        # Преобразуем результат в список словарей
        workers = [model_to_dict(worker) for worker in query]
        return workers
    raise HTTPException(status_code=400, detail="Invalid filter")


# Создаем конечную точку для создания нового работника
@app.post("/worker", response_model=Worker)
async def create_worker(worker: Worker = Body(...)):
    # Создаем новую запись в таблице Worker с данными из тела запроса
    worker = Worker.create(**worker.dict())
    # Преобразуем результат в словарь
    worker = model_to_dict(worker)
    return worker


# Создаем конечную точку для обновления существующего работника по id
@app.put("/worker/{id}", response_model=Worker)
async def update_worker(id: int = Path(...), worker: Worker = Body(...)):
    # Ищем запись по id в таблице Worker
    try:
        old_worker = Worker.get_by_id(id)
    except DoesNotExist:
        # Если записи нет, возвращаем ошибку 404
        raise HTTPException(status_code=404, detail="Worker not found")
    # Обновляем запись с данными из тела запроса
    old_worker.update(**worker.dict()).execute()
    # Преобразуем результат в словарь
    worker = model_to_dict(old_worker)
    return worker


# Создаем конечную точку для обновления нескольких работников по списку id
@app.put("/worker/multiple", response_model=List[Worker])
async def update_multiple_workers(filter: dict = Body(...), worker: Worker = Body(...)):
    if "id" in filter and isinstance(filter["id"], list):
        ids = filter["id"]
        # Получаем все записи из таблицы Worker, у которых id в списке ids
        query = Worker.select().where(Worker.id.in_(ids))
        # Обновляем все записи с данными из тела запроса
        query.update(**worker.dict()).execute()
        # Преобразуем результат в список словарей
        workers = [model_to_dict(worker) for worker in query]
        return workers
    raise HTTPException(status_code=400, detail="Invalid filter")


# Создаем конечную точку для удаления одного работника по id
@app.delete("/worker/{id}")
async def delete_worker(id: int = Path(...)):
    # Ищем запись по id в таблице Worker
    try:
        worker = Worker.get_by_id(id)
    except DoesNotExist:
        # Если записи нет, возвращаем ошибку 404
        raise HTTPException(status_code=404, detail="Worker not found")
    # Удаляем запись из таблицы
    worker.delete_instance()
    return {"message": "Worker deleted"}


# Создаем конечную точку для удаления нескольких работников по списку id
@app.delete("/worker/multiple")
async def delete_multiple_workers(filter: dict = Body(...)):
    # Проверяем, есть ли в фильтре ключ "id" со списком id
    if "id" in filter and isinstance(filter["id"], list):
        ids = filter["id"]
        # Ищем и удаляем работников с данными id
        result = []
        for id in ids:
            try:
                # Находим запись по id в таблице Worker
                worker = Worker.get_by_id(id)
                # Удаляем запись из таблицы
                worker.delete_instance()
                # Добавляем запись в результат
                result.append(model_to_dict(worker))
            except DoesNotExist:
                # Если записи нет, пропускаем ее
                pass
        return {"message": "Workers deleted", "data": result}
    # Если нет, возвращаем ошибку
    raise HTTPException(status_code=400, detail="Invalid filter")