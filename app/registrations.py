"""Rota de inscrição a completar na atividade 3."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db_session import get_session
from app.models import Event, Registration, User


router = APIRouter()


class RegistrationInput(BaseModel):
    user_id: int


@router.post("/events/{event_id}/registrations", status_code=201)
def register(event_id: int, data: RegistrationInput, session: Session = Depends(get_session)):
    # procura o evento informado na url
    event = session.get(Event, event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="evento nao encontrado")

    # procura o usuario informado no json
    user = session.get(User, data.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="usuario nao encontrado")

    # confere se esse usuario ja esta inscrito no evento
    registration = session.scalar(
        select(Registration).where(
            Registration.event_id == event_id,
            Registration.user_id == data.user_id,
        )
    )
    if registration is not None:
        raise HTTPException(status_code=409, detail="usuario ja esta inscrito")

    # conta as inscricoes para saber se ainda existe vaga
    registrations_count = session.scalar(
        select(func.count()).select_from(Registration).where(Registration.event_id == event_id)
    )
    if registrations_count >= event.capacity:
        raise HTTPException(status_code=409, detail="evento lotado")

    # grava a nova inscricao somente depois das validacoes
    registration = Registration(event_id=event_id, user_id=data.user_id)
    session.add(registration)
    session.commit()

    # responde com os dados principais da inscricao
    return {"event_id": event_id, "user_id": data.user_id}
