"""Dependências injetadas nas rotas pelo FastAPI (`Depends`)."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db

SessaoDB = Annotated[Session, Depends(get_db)]
