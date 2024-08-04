import os
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import timedelta, datetime
from jose import jwt
from dotenv import load_dotenv

from .dependencies import get_db, get_current_user, check_admin
from .models import Base, engine, User, Permission
from .schemas import UserCreate, UserUpdate, UserResponse, UserLogin, Token, PermissionCreate, PermissionResponse
from .utils import (
    get_password_hash, verify_password, create_access_token, 
    verify_access_token, is_token_blacklisted, 
    ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM, blacklist_token
)
from .crud import create_user, get_user, get_users, update_user, delete_user, create_permission, get_permissions
from .init_db import init_db  

load_dotenv()

app = FastAPI()

init_db()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter()

@router.post("/users", response_model=UserResponse)
def create_user_endpoint(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user)

@router.get("/users", response_model=List[UserResponse], dependencies=[Depends(get_current_user), Depends(check_admin)])
def read_users(skip: int = 0, limit: int = 10, sort_by: str = "created_at", db: Session = Depends(get_db)):
    users = get_users(db, skip=skip, limit=limit, sort_by=sort_by)
    return [UserResponse.from_orm(user) for user in users]

@router.get("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_user)])
def read_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized to access this user's data")
    return UserResponse.from_orm(user)

@router.put("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_user)])
def update_user_endpoint(user_id: int, user: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_user = get_user(db, user_id=user_id)
    if existing_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if existing_user.id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized to update this user's data")
    updated_user = update_user(db, user_id, user)
    return UserResponse.from_orm(updated_user)

@router.delete("/users/{user_id}", response_model=UserResponse, dependencies=[Depends(get_current_user)])
def delete_user_endpoint(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing_user = get_user(db, user_id=user_id)
    if existing_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if existing_user.id != current_user.id and current_user.role != "Admin":
        raise HTTPException(status_code=403, detail="Not authorized to delete this user")
    deleted_user = delete_user(db, user_id)
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
        blacklist_token(jti, ttl)
    return {"msg": "Successfully logged out"}

@router.post("/permissions", response_model=PermissionResponse, dependencies=[Depends(get_current_user), Depends(check_admin)])
def create_permission_endpoint(permission: PermissionCreate, db: Session = Depends(get_db)):
    return create_permission(db, permission)

@router.get("/permissions/{role}", response_model=List[PermissionResponse], dependencies=[Depends(get_current_user), Depends(check_admin)])
def get_permissions_endpoint(role: str, db: Session = Depends(get_db)):
    permissions = get_permissions(db, role)
    return [PermissionResponse.from_orm(permission) for permission in permissions]

@router.get("/admin", dependencies=[Depends(get_current_user), Depends(check_admin)])
def admin_only_endpoint():
    return {"message": "This is an admin only endpoint"}

@router.post("/users/{user_id}/make_admin", response_model=UserResponse, dependencies=[Depends(get_current_user), Depends(check_admin)])
def make_admin(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id=user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.role = "Admin"
    db.commit()
    db.refresh(user)
    return UserResponse.from_orm(user)

app.include_router(router, prefix="/api")

if __name__ == "__main__":
    init_db()  
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
