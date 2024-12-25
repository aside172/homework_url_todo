from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import sqlite3

app = FastAPI()

DATABASE = "todo.db"


class TodoItem(BaseModel):
    title: str
    description: str = None
    completed: bool = False


def initialize_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN NOT NULL
        )
        """)
    conn.close()


@app.on_event("startup")
def startup():
    initialize_db()


@app.get("/")
def read_root():
    return {
        "message": "Добро пожаловать в TODO API!",
        "endpoints": {
            "POST /items": "Создать новую задачу.",
            "GET /items": "Получить список всех задач.",
            "GET /items/{item_id}": "Получить задачу по ID.",
            "PUT /items/{item_id}": "Обновить задачу по ID.",
            "DELETE /items/{item_id}": "Удалить задачу по ID."
        },
        "documentation": "/docs"
    }


@app.post("/items", status_code=201)
def create_todo(item: TodoItem):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO todos (title, description, completed) VALUES (?, ?, ?)",
                       (item.title, item.description, item.completed))
        conn.commit()
        item_id = cursor.lastrowid
    return {"id": item_id, "message": "Todo item created successfully"}


@app.get("/items")
def get_todos():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM todos")
        todos = cursor.fetchall()
    return [{"id": row[0], "title": row[1], "description": row[2], "completed": row[3]} for row in todos]


@app.get("/items/{item_id}")
def get_todo(item_id: int):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM todos WHERE id = ?", (item_id,))
        todo = cursor.fetchone()
        if not todo:
            raise HTTPException(status_code=404, detail="Todo item not found")
    return {"id": todo[0], "title": todo[1], "description": todo[2], "completed": todo[3]}


@app.put("/items/{item_id}")
def update_todo(item_id: int, item: TodoItem):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE todos SET title = ?, description = ?, completed = ?
        WHERE id = ?
        """, (item.title, item.description, item.completed, item_id))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo item not found")
    return {"message": "Todo item updated successfully"}


@app.delete("/items/{item_id}")
def delete_todo(item_id: int):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM todos WHERE id = ?", (item_id,))
        conn.commit()
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Todo item not found")
    return {"message": "Todo item deleted successfully"}
