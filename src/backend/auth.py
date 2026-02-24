from fastapi import HTTPException, status, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Optional
import jwt
import json
import base64
from config import settings


security = HTTPBearer(auto_error=False)


class TokenData(BaseModel):
    user_id: Optional[str] = None


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """
    Verify JWT token and extract user_id
    Supports both proper JWT and simple base64 encoded tokens for demo mode
    """
    if credentials is None:
        return None

    token = credentials.credentials

    try:
        # First try proper JWT decode
        payload = jwt.decode(
            token,
            settings.better_auth_secret,
            algorithms=["HS256"]
        )

        # Extract user_id from the token
        user_id = payload.get("userId") or payload.get("sub") or payload.get("id")

        # Validate that extracted user_id is not empty string or None
        if not user_id or user_id.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user identity",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.PyJWTError, Exception):
        # Try base64 decode for demo tokens
        try:
            decoded = base64.b64decode(token).decode('utf-8')
            payload = json.loads(decoded)
            user_id = payload.get("userId") or payload.get("sub") or payload.get("id")
            if user_id:
                # Validate that extracted user_id is not empty string or None
                if not user_id or user_id.strip() == "":
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid user identity",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                return user_id
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user_id(token: Optional[str] = Depends(verify_token)) -> str:
    """
    Get the current user's ID from the token
    Falls back to 'demo-user' if no valid token provided
    """
    if token:
        return token
    # For demo purposes, allow unauthenticated access with demo-user
    return "demo-user"
