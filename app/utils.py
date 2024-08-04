import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import redis
import uuid
from .schemas import TokenData  
import logging
from dotenv import load_dotenv

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

redis_url = os.getenv("REDIS_URL")

try:
    r = redis.from_url(redis_url)
    r.ping()
    redis_available = True
except redis.ConnectionError:
    logging.warning("Redis server is not available. Token blacklist feature is disabled.")
    redis_available = False

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        jti = payload.get("jti")
        if redis_available and is_token_blacklisted(jti):
            raise credentials_exception
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    return token_data

def is_token_blacklisted(jti):
    if not redis_available:
        return False
    return r.exists(jti) == 1

def blacklist_token(jti, ttl):
    if redis_available:
        try:
            r.set(jti, "true", ex=int(ttl))
        except redis.ConnectionError:
            logging.error("Failed to connect to Redis for blacklisting token.")
