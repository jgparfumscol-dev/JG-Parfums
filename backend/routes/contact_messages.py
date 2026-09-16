from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from database import get_db
from main import limiter
from middleware.auth import get_current_admin
from models.contact_message import ContactMessage
from models.user import User
from schemas.contact_message import ContactMessageCreate, ContactMessageResponse, ContactMessageUpdate

router = APIRouter(prefix="/contact-messages", tags=["contact-messages"])


@router.post("", response_model=ContactMessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_contact_message(request: Request, payload: ContactMessageCreate, db: Session = Depends(get_db)):
    message = ContactMessage(**payload.model_dump())
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


@router.get("", response_model=list[ContactMessageResponse])
def list_contact_messages(db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)):
    return db.query(ContactMessage).order_by(ContactMessage.created_at.desc()).all()


@router.put("/{message_id}", response_model=ContactMessageResponse)
def update_contact_message(
    message_id: int,
    payload: ContactMessageUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensaje no encontrado")
    message.is_read = payload.is_read
    db.commit()
    db.refresh(message)
    return message


@router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_contact_message(
    message_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    message = db.query(ContactMessage).filter(ContactMessage.id == message_id).first()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mensaje no encontrado")
    db.delete(message)
    db.commit()
