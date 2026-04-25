from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List
from app.db.database import get_db
from app.db.models import User, UserRole
from app.core.auth import hash_password, TokenData
from app.core.permissions import require_role

router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "viewer"


class UserUpdate(BaseModel):
    role: str = None
    password: str = None


class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    created_at: str

    class Config:
        from_attributes = True


@router.get("", response_model=List[UserResponse], dependencies=[Depends(require_role(["admin"]))])
async def list_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return users


@router.post("", response_model=UserResponse, dependencies=[Depends(require_role(["admin"]))])
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate role
    try:
        role = UserRole(user_data.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role. Must be 'viewer', 'curator', or 'admin'",
        )

    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        role=role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: TokenData = Depends(require_role(["admin"])),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Prevent non-admins from updating other users
    if current_user.role != "admin" and current_user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own password",
        )

    if user_update.role and current_user.role == "admin":
        try:
            role = UserRole(user_update.role)
            user.role = role
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role",
            )

    if user_update.password:
        user.hashed_password = hash_password(user_update.password)

    db.commit()
    db.refresh(user)
    return user
