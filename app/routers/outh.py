from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr

from app.auth_utils import hash_password, verify_password
from app.database import get_db_connection

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(data: RegisterRequest):
    name = data.name.strip()
    email = data.email.lower().strip()

    if not name:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    password_hash = hash_password(data.password)
    conn = get_db_connection()

    try:
        existing_user = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email,)
        ).fetchone()

        if existing_user:
            raise HTTPException(status_code=409, detail="Email is already registered")

        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()

        return {
            "message": "Account created successfully",
            "user_id": cursor.lastrowid,
        }
    finally:
        conn.close()


@router.post("/login")
def login(request: Request, data: LoginRequest):
    conn = get_db_connection()

    try:
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (data.email.lower().strip(),),
        ).fetchone()
    finally:
        conn.close()

    if not user or not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    request.session["user_id"] = user["id"]
    request.session["user_name"] = user["name"]

    return {
        "message": "Login successful",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        },
    }


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logout successful"}