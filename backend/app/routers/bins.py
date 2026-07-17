from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Bin
from app.schemas import BinOut

router = APIRouter(prefix="/api/bins", tags=["bins"])


@router.post("", response_model=BinOut, status_code=201)
def create_bin(db: Session = Depends(get_db)):
    b = Bin()
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


@router.get("/{bin_id}", response_model=BinOut)
def get_bin(bin_id: str, db: Session = Depends(get_db)):
    b = db.get(Bin, bin_id)
    if b is None:
        raise HTTPException(status_code=404, detail="bin not found")
    return b
