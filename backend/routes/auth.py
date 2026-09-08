import logging
import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from main import limiter
from middleware.auth import create_access_token, get_client_ip, get_current_user, hash_password, verify_password
from models.password_reset import PasswordResetToken
from models.user import User
from schemas.auth import (
    ForgotPasswordRequest,
    GenericMessageResponse,
    LoginRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from services.email_service import email_bienvenida, email_reset_password

logger = logging.getLogger("jg_parfums.auth")

router = APIRouter(prefix="/auth", tags=["auth"])

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8000")

# Mensaje genérico deliberado: no debe distinguir "email no existe" de "password incorrecta".
_INVALID_CREDENTIALS = "Email o contraseña incorrectos"


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing is not None:
        # Mismo status/forma que un registro exitoso fallaría de otra forma no lo hace;
        # se responde 400 con mensaje genérico para no confirmar detalles de la cuenta.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo completar el registro")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    email_bienvenida(user.email, user.full_name)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        logger.warning("Intento de login fallido, ip=%s", get_client_ip(request))
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_CREDENTIALS)
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=_INVALID_CREDENTIALS)

    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/forgot-password", response_model=GenericMessageResponse)
@limiter.limit("5/minute")
def forgot_password(request: Request, payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    generic_response = GenericMessageResponse(
        message="Si el email existe, te enviamos un enlace para restablecer la contraseña"
    )
    user = db.query(User).filter(User.email == payload.email).first()
    if user is None:
        return generic_response  # no revela si el email existe

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )
    db.add(reset_token)
    db.commit()

    reset_url = f"{FRONTEND_URL}/reset-password.html?token={token}"
    email_reset_password(user.email, reset_url)
    return generic_response


@router.post("/reset-password", response_model=GenericMessageResponse)
@limiter.limit("5/minute")
def reset_password(request: Request, payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    reset_token = db.query(PasswordResetToken).filter(PasswordResetToken.token == payload.token).first()
    now = datetime.now(timezone.utc)
    if reset_token is None or reset_token.used or reset_token.expires_at < now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Enlace inválido o vencido")

    user = db.query(User).filter(User.id == reset_token.user_id).first()
    user.password_hash = hash_password(payload.new_password)
    reset_token.used = True
    db.commit()

    return GenericMessageResponse(message="Contraseña actualizada")
