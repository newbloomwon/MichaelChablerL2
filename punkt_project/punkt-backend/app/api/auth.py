from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from app.core.auth import verify_password, create_access_token
from app.core.database import get_db_conn
from app.models.api import APIResponse
from datetime import datetime
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
async def login(
    credentials: LoginRequest,
    conn = Depends(get_db_conn)
):
    user = await conn.fetchrow(
        "SELECT id, username, password_hash, tenant_id FROM users WHERE username = $1",
        credentials.username
    )
    
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(
        data={"sub": user["id"], "tenant_id": user["tenant_id"]}
    )
    
    return APIResponse(
        success=True,
        data={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user["id"],
                "username": user["username"],
                "tenant_id": user["tenant_id"]
            }
        },
        timestamp=datetime.utcnow()
    )

@router.get("/me")
async def get_me(request: Request, conn = Depends(get_db_conn)):
    # Get user_id from request state (set by tenant middleware)
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    user = await conn.fetchrow(
        "SELECT id, username, tenant_id FROM users WHERE id = $1",
        user_id
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return APIResponse(
        success=True,
        data={
            "id": user["id"],
            "username": user["username"],
            "tenant_id": user["tenant_id"]
        },
        timestamp=datetime.utcnow()
    )
