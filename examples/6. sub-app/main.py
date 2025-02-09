import uvicorn
from app2.main import app as app2
from app1.main import app as app1


from fastapi import FastAPI

app = FastAPI()


app.mount('/app1', app1)
app.mount('/app2', app2)


if __name__ == '__main__':
    uvicorn.run('main:app', port=8002, reload=True)
