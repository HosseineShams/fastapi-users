from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .models import User, Permission
from .schemas import UserCreate, UserUpdate, UserResponse, PermissionCreate, PermissionResponse
from .utils import get_password_hash
from fastapi import HTTPException, status

def create_user(db: Session, user: UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = User(username=user.username, email=user.email, password=hashed_password, role="User")
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )
    return UserResponse.from_orm(db_user)

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 10, sort_by: str = "created_at"):
    if sort_by not in ['username', 'created_at']:
        sort_by = 'created_at'
    return db.query(User).order_by(sort_by).offset(skip).limit(limit).all()

def update_user(db: Session, user_id: int, user: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return None
    db_user.username = user.username
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        return None
    db.delete(db_user)
    db.commit()
    return db_user

def create_permission(db: Session, permission: PermissionCreate):
    db_permission = Permission(role=permission.role, endpoint=permission.endpoint, method=permission.method)
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return PermissionResponse.from_orm(db_permission)

def get_permissions(db: Session, role: str):
    return db.query(Permission).filter(Permission.role == role).all()
