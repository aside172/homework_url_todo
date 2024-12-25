from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
import sqlite3
import string
import random

app = FastAPI()

DATABASE = "shorturl.db"
BASE_URL = "http://localhost:8001/"


class URLRequest(BaseModel):
    url: HttpUrl


class URLResponse(BaseModel):
    short_url: str


def initialize_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            short_id TEXT UNIQUE,
            full_url TEXT
        )
        """)
    conn.close()


def generate_short_id(length=6):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


@app.on_event("startup")
def startup():
    initialize_db()


@app.get("/")
def read_root():
    return {
        "message": "Добро пожаловать в API для сокращения ссылок!",
        "endpoints": {
            "POST /shorten": "Создать короткую ссылку для полного URL.",
            "GET /{short_id}": "Перенаправить на полный URL по короткому идентификатору.",
            "GET /stats/{short_id}": "Получить информацию о полном URL по короткой ссылке."
        },
        "documentation": "/docs"
    }



@app.post("/shorten", response_model=URLResponse)
def shorten_url(request: URLRequest):
    short_id = generate_short_id()
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO urls (short_id, full_url) VALUES (?, ?)", (short_id, str(request.url)))
            conn.commit()
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="URL already exists.")
    return URLResponse(short_url=f"{BASE_URL}{short_id}")



@app.get("/{short_id}")
def redirect_to_url(short_id: str):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT full_url FROM urls WHERE short_id = ?", (short_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="URL not found.")
    return {"url": result[0]}


@app.get("/stats/{short_id}")
def get_url_stats(short_id: str):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT full_url FROM urls WHERE short_id = ?", (short_id,))
        result = cursor.fetchone()
        if not result:
            raise HTTPException(status_code=404, detail="URL not found.")
    return {"short_id": short_id, "full_url": result[0]}
