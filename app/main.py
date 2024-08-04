from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta, datetime
from jose import jwt 

from app.dependencies import get_db, get_current_user
from app.models import Base, engine, User
from app.schemas import UserCreate, UserUpdate, UserResponse, UserLogin, Token
from app.utils import (
    get_password_hash, verify_password, create_access_token, 
    verify_access_token, is_token_blacklisted, 
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM, r 
)
from app.crud import create_user, get_user, get_users, update_user, delete_user

app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter()

@router.post("/users", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)

@router.get("/users", response_model=List[UserResponse])
def read_users(skip: int = 0, limit: int = 10, sort_by: str = "created_at", db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit, sort_by=sort_by)
    return [UserResponse.from_orm(user) for user in users]

@router.get("/users/{user_id}", response_model=UserResponse)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)

@router.put("/users/{user_id}", response_model=UserResponse)
def update_user_endpoint(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    updated_user = update_user(db, user_id, user)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(updated_user)

@router.delete("/users/{user_id}", response_model=UserResponse)
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db)):
    deleted_user = delete_user(db, user_id)
    if deleted_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(deleted_user)

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    jti = payload.get("jti")
    exp = payload.get("exp")
    if jti and exp:
        ttl = exp - datetime.utcnow().timestamp()
        r.set(jti, "true", ex=int(ttl))
    return {"msg": "Successfully logged out"}

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
