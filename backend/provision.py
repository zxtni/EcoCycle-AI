import os

from pydantic import EmailStr, TypeAdapter
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.auth import password_hash
from backend.db import User, engine


def provision():
    email = str(TypeAdapter(EmailStr).validate_python(os.environ["ECO_ADMIN_EMAIL"])).lower()
    password = os.environ["ECO_ADMIN_PASSWORD"]
    if not 14 <= len(password) <= 128:
        raise SystemExit("Set a unique administrator password of 14 to 128 characters.")
    with Session(engine) as db:
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            raise SystemExit("This email already exists. Use a new address for the initial administrator.")
        db.add(User(email=email, password=password_hash(password), name="Municipality Admin", role="admin"))
        db.commit()
    print("Municipality administrator created.")


if __name__ == "__main__":
    provision()
