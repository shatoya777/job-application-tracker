"""Small MySQL access layer for the Job Application Tracker."""

import os
from typing import Any, Iterable

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Open a new connection using values from the local .env file."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "job_tracker"),
        charset="utf8mb4",
        autocommit=False,
    )


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    """Return all rows as dictionaries."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, tuple(params))
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def fetch_one(sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    """Return one row as a dictionary, or None when no row matches."""
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(sql, tuple(params))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def execute_write(sql: str, params: Iterable[Any] = ()) -> tuple[int | None, int]:
    """Execute INSERT, UPDATE, or DELETE and commit only on success.

    Returns (last_insert_id, affected_rows).
    """
    connection = get_connection()
    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        connection.commit()
        return cursor.lastrowid, cursor.rowcount
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
