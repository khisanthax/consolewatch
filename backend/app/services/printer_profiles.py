from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Printer, utc_now
from app.schemas.printers import PrinterCreate, PrinterUpdate


def list_printers(db: Session) -> list[Printer]:
    return list(db.scalars(select(Printer).order_by(Printer.name.asc(), Printer.id.asc())).all())


def get_printer(db: Session, printer_id: int) -> Printer | None:
    return db.get(Printer, printer_id)


def create_printer(db: Session, payload: PrinterCreate) -> Printer:
    printer = Printer(
        name=payload.name.strip(),
        base_url=str(payload.base_url).rstrip("/"),
        api_key=payload.api_key or None,
        is_enabled=payload.is_enabled,
        console_watch_enabled=payload.console_watch_enabled,
        retention_hours=payload.retention_hours,
    )
    db.add(printer)
    db.commit()
    db.refresh(printer)
    return printer


def update_printer(db: Session, printer: Printer, payload: PrinterUpdate) -> Printer:
    updates = payload.model_dump(exclude_unset=True)
    if "name" in updates and updates["name"] is not None:
        printer.name = updates["name"].strip()
    if "base_url" in updates and updates["base_url"] is not None:
        printer.base_url = str(updates["base_url"]).rstrip("/")
    if "api_key" in updates:
        printer.api_key = updates["api_key"] or None
    if "is_enabled" in updates and updates["is_enabled"] is not None:
        printer.is_enabled = updates["is_enabled"]
    if "console_watch_enabled" in updates and updates["console_watch_enabled"] is not None:
        printer.console_watch_enabled = updates["console_watch_enabled"]
    if "retention_hours" in updates and updates["retention_hours"] is not None:
        printer.retention_hours = updates["retention_hours"]

    printer.updated_at = utc_now()
    db.commit()
    db.refresh(printer)
    return printer


def delete_printer(db: Session, printer: Printer) -> None:
    db.delete(printer)
    db.commit()
