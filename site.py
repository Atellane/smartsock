from uvicorn import run
from sqlite3 import Error
from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from db import Db


db = Db("site.db")
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates/")


@app.get("/")
def index(request: Request) -> str:
    return templates.TemplateResponse("index.html", {'request': request})


@app.get("/accueil.html")
def acceuil_compte(request: Request) -> str:
    return templates.TemplateResponse("accueil.html", {'request': request})


@app.get("/creation.html")
def creation(request: Request) -> str:
    return templates.TemplateResponse("creation.html", {'request': request})


@app.get("/connexion.html")
def connexion(request: Request) -> str:
    return templates.TemplateResponse("connexion.html", {'request': request})


@app.post("/create_user")
def create_user(username: str = Form(...), password: str = Form(...)) -> dict:
    try: 
        db.create_user(username, password)
        return JSONResponse(content={"error": None})
    except Error as e:
        return JSONResponse(content={"error": str(e)})


@app.post("/connect_user")
def connect_user(username: str = Form(...), password: str = Form(...)) -> dict:
    try: 
        auth_token = db.connect_user(username, password)
        return JSONResponse(content={"auth_token": auth_token})
    except Error:
        return JSONResponse(content={"auth_token": None}) # correspond à mot de passe incorrecte


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=80)
