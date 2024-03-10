import uvicorn

from . import app


uvicorn.run("WebAPI:app", host='localhost', port=8888, reload=True)
