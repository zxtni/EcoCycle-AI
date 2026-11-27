import base64
import hashlib
import hmac
import os
import secrets
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.db import LoginSession, User, database, now

router = APIRouter(prefix="/api/auth", tags=["identity"])
DB = Annotated[Session, Depends(database)]
COOKIE = "eco_session"


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)


class Registration(Credentials):
    name: str = Field(min_length=1, max_length=80, pattern=r"\S")


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64 * 1024**2)
    return base64.b64encode(salt + digest).decode()


def current(db: DB, eco_session: Annotated[str | None, Cookie()] = None) -> User:
    session = db.get(LoginSession, hashlib.sha256((eco_session or "").encode()).hexdigest())
    if session and session.expires > now():
        user = db.get(User, session.user_id)
        if user:
            return user
    raise HTTPException(401, "Sign in to continue.")


Citizen = Annotated[User, Depends(current)]


def require_admin(user: Citizen) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Municipality administrator access required.")
    return user


Admin = Annotated[User, Depends(require_admin)]


def profile(user: User):
    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "synthetic": user.synthetic,
    }


def issue(db: Session, user: User, response: Response):
    token = secrets.token_urlsafe(40)
    db.add(
        LoginSession(
            token=hashlib.sha256(token.encode()).hexdigest(),
            user_id=user.id,
            expires=now() + timedelta(days=7),
        )
    )
    db.commit()
    response.set_cookie(
        COOKIE,
        token,
        max_age=604800,
        httponly=True,
        secure=os.getenv("APP_ENV") == "production",
        samesite="lax",
        path="/",
    )
    return profile(user)


@router.post("/register", status_code=201)
def register(body: Registration, db: DB, response: Response):
    user = User(name=body.name.strip(), email=str(body.email).lower(), password=password_hash(body.password))
    db.add(user)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "This email already has an account.")
    return issue(db, user, response)


@router.post("/login")
def login(body: Credentials, db: DB, response: Response):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    stored = user.password if user and user.password else ""
    salt = base64.b64decode(stored)[:16] if stored else None
    check = password_hash(body.password, salt)
    if not user or not hmac.compare_digest(stored, check):
        raise HTTPException(401, "Email or password is incorrect.")
    return issue(db, user, response)


@router.get("/me")
def me(user: Citizen):
    return profile(user)


@router.post("/logout")
def logout(db: DB, response: Response, eco_session: Annotated[str | None, Cookie()] = None):
    row = db.get(LoginSession, hashlib.sha256((eco_session or "").encode()).hexdigest())
    if row:
        db.delete(row)
        db.commit()
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}
