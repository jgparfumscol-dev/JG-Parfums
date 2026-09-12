from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin
from models.site_settings import SiteSettings
from models.user import User
from schemas.settings import SiteSettingsResponse, SiteSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


def _get_or_create(db: Session) -> SiteSettings:
    settings = db.query(SiteSettings).filter(SiteSettings.id == 1).first()
    if settings is None:
        settings = SiteSettings(id=1)
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=SiteSettingsResponse)
def get_settings(db: Session = Depends(get_db)):
    return _get_or_create(db)


@router.put("", response_model=SiteSettingsResponse)
def update_settings(
    payload: SiteSettingsUpdate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    settings = _get_or_create(db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings, field, value)
    db.commit()
    db.refresh(settings)
    return settings
