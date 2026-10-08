"""FastAPI backend. Run: python -m uvicorn app:app --reload"""
from fastapi import FastAPI, Request, Query as QueryParam
from fastapi.responses import JSONResponse
from mysql.connector import Error as DatabaseError
from pydantic import BaseModel, Field
from database import get_schema, execute_query, check_connection, database_error_message, list_databases
from query_generator import generate_sql

app = FastAPI(title='AI SQL Generator', version='1.0')


class Question(BaseModel):
    # FastAPI rejects missing or oversized input before calling our function.
    question: str = Field(min_length=1, max_length=2000)
    databases: list[str] | None = Field(default=None, max_length=100)


class Query(BaseModel):
    sql: str = Field(min_length=1, max_length=10000)
    databases: list[str] | None = Field(default=None, max_length=100)


@app.exception_handler(ValueError)
async def input_error(request: Request, error: ValueError):
    return JSONResponse(status_code=400, content={'detail': str(error)})


@app.exception_handler(DatabaseError)
async def database_error(request: Request, error: DatabaseError):
    return JSONResponse(status_code=400, content={
        'detail': database_error_message(error)})


@app.get('/connection')
def connection():
    return check_connection()


@app.get('/schema')
def schema(databases: list[str] | None = QueryParam(default=None)):
    return get_schema(databases)


@app.get('/databases')
def databases():
    return {'databases': list_databases()}


@app.post('/generate-sql')
def generate(body: Question):
    if not body.question.strip():
        raise ValueError('Enter a question first.')
    schema = get_schema(body.databases)  # Refresh metadata on every generation request.
    if not schema['tables']:
        raise ValueError('No tables are visible. Check the database name and SELECT permissions.')
    return {'sql': generate_sql(body.question.strip(), schema)}


@app.post('/execute-query')
def execute(body: Query):
    return execute_query(body.sql, body.databases)
