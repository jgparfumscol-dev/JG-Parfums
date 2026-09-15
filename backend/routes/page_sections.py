from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_admin, get_optional_user
from models.page_section import PageSection
from models.page_section_history import PageSectionHistory
from models.user import User
from schemas.page_section import (
    PageSectionCreate,
    PageSectionHistoryResponse,
    PageSectionMove,
    PageSectionResponse,
    PageSectionUpdate,
    validate_announcement_bar_content,
)

router = APIRouter(prefix="/page-sections", tags=["page-sections"])

# Colombia no usa horario de verano: comparar como "hora de pared" de Bogotá
# sin tzinfo evita mezclar naive/aware (el <input type="datetime-local"> del
# admin manda fechas sin offset, asumiendo que el admin está en Colombia).
BOGOTA_TZ = ZoneInfo("America/Bogota")


def _validation_http_error(exc: ValidationError) -> HTTPException:
    # exc.errors() trae un "ctx" con la excepción de Python original (no es
    # serializable a JSON) cuando el error viene de un @field_validator/
    # @model_validator — se arma la lista a mano con solo lo serializable.
    errors = [{"loc": list(e["loc"]), "msg": e["msg"], "type": e["type"]} for e in exc.errors()]
    return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=errors)


def _assert_single_top_announcement(
    db: Session, page: str, content: dict, *, exclude_id: int | None = None
) -> None:
    """Como máximo una barra de anuncios activa en position="top" por
    página — dos al mismo tiempo competirían por el mismo lugar arriba del
    header. "inline" no tiene este límite, se comporta como cualquier otra
    sección libre."""
    if content.get("position") != "top":
        return
    query = db.query(PageSection).filter(
        PageSection.page == page,
        PageSection.type == "announcement_bar",
        PageSection.is_active.is_(True),
    )
    if exclude_id is not None:
        query = query.filter(PageSection.id != exclude_id)
    for existing in query.all():
        if (existing.content or {}).get("position") == "top":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una barra de anuncios activa arriba del header en esta página. "
                "Cámbiala a 'inline' o edita la existente en vez de crear otra.",
            )


def _message_is_live(message: dict, now_bogota: datetime) -> bool:
    if not message.get("is_active", True):
        return False
    start = message.get("start_date")
    end = message.get("end_date")
    if start:
        start_dt = datetime.fromisoformat(start)
        if start_dt.tzinfo is not None:
            start_dt = start_dt.astimezone(BOGOTA_TZ).replace(tzinfo=None)
        if start_dt > now_bogota:
            return False
    if end:
        end_dt = datetime.fromisoformat(end)
        if end_dt.tzinfo is not None:
            end_dt = end_dt.astimezone(BOGOTA_TZ).replace(tzinfo=None)
        if end_dt < now_bogota:
            return False
    return True


def _snapshot(section: PageSection, action: str, db: Session) -> None:
    """Guarda una copia autocontenida del estado actual de `section`. No
    depende de que la fila original siga existiendo después — por eso el
    historial sobrevive a un borrado real.
    """
    db.add(
        PageSectionHistory(
            section_id=section.id,
            page=section.page,
            key=section.key,
            type=section.type,
            content=section.content,
            is_active=section.is_active,
            position=section.position,
            action=action,
        )
    )


# Los endpoints de /history van antes de /{section_id}: Starlette resuelve
# rutas en orden de registro, así que si /{section_id} (int) quedara primero,
# "history" se intentaría parsear como section_id y rompería con 422 — el
# mismo bug que ya pasó una vez con los webhooks de pagos.
@router.get("/history", response_model=list[PageSectionHistoryResponse])
def list_page_section_history(
    page: str,
    limit: int = 50,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    return (
        db.query(PageSectionHistory)
        .filter(PageSectionHistory.page == page)
        .order_by(PageSectionHistory.created_at.desc(), PageSectionHistory.id.desc())
        .limit(limit)
        .all()
    )


@router.post("/history/{history_id}/restore", response_model=PageSectionResponse)
def restore_page_section(
    history_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    entry = db.query(PageSectionHistory).filter(PageSectionHistory.id == history_id).first()
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Versión no encontrada")

    section = (
        db.query(PageSection).filter(PageSection.id == entry.section_id).first()
        if entry.section_id is not None
        else None
    )
    if section is not None:
        # La sección todavía existe: se le devuelve el contenido de esa versión.
        section.content = entry.content
        section.is_active = entry.is_active
    else:
        # La sección fue borrada: reaparece como una fila nueva, en el mismo lugar.
        max_position = (
            db.query(PageSection.position)
            .filter(PageSection.page == entry.page)
            .order_by(PageSection.position.desc())
            .first()
        )
        next_position = (max_position[0] + 1) if max_position else 0
        section = PageSection(
            page=entry.page,
            key=entry.key,
            type=entry.type,
            content=entry.content,
            is_active=entry.is_active,
            is_builtin=entry.key is not None,
            position=entry.position if entry.key is not None else next_position,
        )
        db.add(section)

    db.flush()
    _snapshot(section, "restored", db)
    db.commit()
    db.refresh(section)
    return section


@router.get("", response_model=list[PageSectionResponse])
def list_page_sections(
    page: str,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    # Solo un admin puede pedir secciones ocultas (ej. para reactivarlas en el editor).
    is_admin_request = include_inactive and user is not None and user.is_admin
    query = db.query(PageSection).filter(PageSection.page == page)
    if not is_admin_request:
        query = query.filter(PageSection.is_active.is_(True))
    sections = query.order_by(PageSection.position).all()

    # El público solo ve mensajes vigentes de la barra de anuncios (activos y
    # dentro de su rango de fechas); el admin ve todo para poder editarlo. Se
    # arman respuestas Pydantic nuevas en vez de mutar las filas del ORM —
    # son de solo lectura para este request, así un commit posterior en la
    # misma sesión no termina guardando el contenido filtrado en la base.
    responses = [PageSectionResponse.model_validate(s) for s in sections]
    if not is_admin_request:
        now_bogota = datetime.now(BOGOTA_TZ).replace(tzinfo=None)
        for response in responses:
            if response.type == "announcement_bar":
                messages = response.content.get("messages", [])
                response.content = {
                    **response.content,
                    "messages": [m for m in messages if _message_is_live(m, now_bogota)],
                }
    return responses


@router.post("", response_model=PageSectionResponse, status_code=status.HTTP_201_CREATED)
def create_page_section(
    payload: PageSectionCreate, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    content = payload.content
    if payload.type == "announcement_bar":
        try:
            content = validate_announcement_bar_content(content)
        except ValidationError as exc:
            raise _validation_http_error(exc)
        if payload.is_active:
            _assert_single_top_announcement(db, payload.page, content)

    max_position = (
        db.query(PageSection.position)
        .filter(PageSection.page == payload.page)
        .order_by(PageSection.position.desc())
        .first()
    )
    next_position = (max_position[0] + 1) if max_position else 0

    section = PageSection(
        page=payload.page, type=payload.type, content=content, is_active=payload.is_active, position=next_position
    )
    db.add(section)
    db.flush()
    _snapshot(section, "created", db)
    db.commit()
    db.refresh(section)
    return section


@router.put("/{section_id}", response_model=PageSectionResponse)
def update_page_section(
    section_id: int,
    payload: PageSectionUpdate,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")

    updates = payload.model_dump(exclude_unset=True)
    if section.type == "announcement_bar":
        will_be_active = updates.get("is_active", section.is_active)
        if "content" in updates:
            try:
                updates["content"] = validate_announcement_bar_content(updates["content"])
            except ValidationError as exc:
                raise _validation_http_error(exc)
            if will_be_active:
                _assert_single_top_announcement(db, section.page, updates["content"], exclude_id=section.id)
        elif will_be_active and "is_active" in updates:
            # Se reactiva sin tocar el content: el content ya guardado define la posición.
            _assert_single_top_announcement(db, section.page, section.content or {}, exclude_id=section.id)

    for field, value in updates.items():
        setattr(section, field, value)
    _snapshot(section, "updated", db)
    db.commit()
    db.refresh(section)
    return section


@router.put("/{section_id}/move", response_model=PageSectionResponse)
def move_page_section(
    section_id: int,
    payload: PageSectionMove,
    db: Session = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")

    siblings = (
        db.query(PageSection)
        .filter(PageSection.page == section.page)
        .order_by(PageSection.position)
        .all()
    )
    index = next(i for i, s in enumerate(siblings) if s.id == section.id)
    neighbor_index = index - 1 if payload.direction == "up" else index + 1
    if 0 <= neighbor_index < len(siblings):
        neighbor = siblings[neighbor_index]
        section.position, neighbor.position = neighbor.position, section.position
        db.commit()
        db.refresh(section)
    return section


@router.delete("/{section_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_page_section(
    section_id: int, db: Session = Depends(get_db), _admin: User = Depends(get_current_admin)
):
    section = db.query(PageSection).filter(PageSection.id == section_id).first()
    if section is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sección no encontrada")
    _snapshot(section, "deleted", db)
    db.delete(section)
    db.commit()
