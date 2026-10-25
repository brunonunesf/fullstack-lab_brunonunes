"""API de eventos usada em todas as etapas do projeto."""

from datetime import date

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import Base, make_engine
from app.db_session import get_session
from app.models import Event, Registration
from app.registrations import router as registrations_router


class EventInput(BaseModel):
    """Dados enviados pelo cliente ao cadastrar um evento."""

    title: str
    date: date
    capacity: int


def event_data(event: Event, session: Session):
    # conta quantas inscricoes ja foram feitas neste evento
    registrations_count = session.scalar(
        select(func.count()).select_from(Registration).where(Registration.event_id == event.id)
    )

    # monta a resposta com os dados do evento e as vagas restantes
    return {
        "id": event.id,
        "title": event.title,
        "date": event.date,
        "capacity": event.capacity,
        "available_slots": event.capacity - registrations_count,
    }


def create_app(database_url: str | None = None) -> FastAPI:
    # usa um banco temporario nos testes e a url recebida quando ela existir
    database_url = database_url or "sqlite://"
    engine = make_engine(database_url)
    Base.metadata.create_all(engine)

    app = FastAPI(title="Eventos do Trilha")
    # guarda o acesso ao banco para as rotas usarem depois
    app.state.engine = engine

    @app.get("/events")
    def list_events(session: Session = Depends(get_session)):
        # pega todos os eventos que estao no banco
        events = session.scalars(select(Event)).all()
        return [event_data(event, session) for event in events]

    @app.get("/events/{event_id}")
    def get_event(event_id: int, session: Session = Depends(get_session)):
        # procura o evento pelo id
        event = session.get(Event, event_id)
        if event is None:
            raise HTTPException(status_code=404, detail="Evento nao encontrado")
        return event_data(event, session)

    @app.post("/events", status_code=201)
    def create_event(data: EventInput, session: Session = Depends(get_session)):
        # impede criar evento sem titulo
        if not data.title.strip():
            raise HTTPException(status_code=422, detail="titulo nao pode ser vazio")

        # impede criar evento com capacidade zero ou negativa
        if data.capacity <= 0:
            raise HTTPException(status_code=422, detail="capacidade deve ser maior que zero")

        # cria o evento com os dados recebidos
        event = Event(title=data.title, date=data.date, capacity=data.capacity)
        session.add(event)
        session.commit()
        session.refresh(event)

        # devolve o evento ja salvo no banco
        return event_data(event, session)

    # adiciona a rota de inscricao na aplicacao
    app.include_router(registrations_router)
    return app


# a api iniciada pelo servidor usa o arquivo events.db
app = create_app("sqlite:///events.db")
