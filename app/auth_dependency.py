import sqlite3
from fastapi import HTTPException, Request, status
from app.database import get_db_connection


def get_current_user(request: Request):
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You must be logged in"
        )

    conn = get_db_connection()
    conn.row_factory = sqlite3.Row

    try:
        user = conn.execute(
            """
            SELECT
                id,
                name,
                email
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        ).fetchone()

    finally:
        conn.close()

    if not user:
        request.session.clear()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User session is invalid"
        )

    return dict(user)