import bcrypt
import jwt
from datetime import datetime, timedelta

    # GENERATES SALT AND ENCRYPT THE PASSWORD
def hash_password(password: str) -> str:
    """Generates a secure password hash using bcrypt."""
    try:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        raise ValueError("Failed to securely hash password.") from e


    # VERIFIES PLAIN PW AND HASHED PW
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies if a plain text password matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
    except (valueError, TypeError):
        return false
    )

    # CREATION OF TOKENS AND VERIFIER
SECRET_KEY = "tu_clave_super_secreta_aqui"
ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: timedelta = timedelta(hours=1)):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None