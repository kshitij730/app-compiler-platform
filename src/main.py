from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .models import CompileRequest, CompileResponse
from .pipeline import AppCompiler

app = FastAPI(title="App Compiler Platform", version="1.0")
compiler = AppCompiler()

app.mount("/static", StaticFiles(directory="src/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    with open("src/static/index.html", "r", encoding="utf-8") as file:
        return file.read()


@app.post("/compile", response_model=CompileResponse)
def compile_app(request: CompileRequest) -> CompileResponse:
    return compiler.compile(request.prompt)
