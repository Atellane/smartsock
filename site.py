from uvicorn import run
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
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


if __name__ == "__main__":
    run(app, host="0.0.0.0", port=80)
