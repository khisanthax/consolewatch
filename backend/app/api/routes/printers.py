from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.printers import PrinterCreate, PrinterRead, PrinterUpdate
from app.services import printer_profiles

router = APIRouter()


@router.get("", response_model=list[PrinterRead])
def list_printers(db: Session = Depends(get_db)):
    return printer_profiles.list_printers(db)


@router.post("", response_model=PrinterRead, status_code=status.HTTP_201_CREATED)
def create_printer(payload: PrinterCreate, db: Session = Depends(get_db)):
    return printer_profiles.create_printer(db, payload)


@router.get("/{printer_id}", response_model=PrinterRead)
def get_printer(printer_id: int, db: Session = Depends(get_db)):
    printer = printer_profiles.get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    return printer


@router.put("/{printer_id}", response_model=PrinterRead)
def update_printer(printer_id: int, payload: PrinterUpdate, db: Session = Depends(get_db)):
    printer = printer_profiles.get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    return printer_profiles.update_printer(db, printer, payload)


@router.delete("/{printer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_printer(printer_id: int, db: Session = Depends(get_db)):
    printer = printer_profiles.get_printer(db, printer_id)
    if printer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Printer not found")
    printer_profiles.delete_printer(db, printer)
