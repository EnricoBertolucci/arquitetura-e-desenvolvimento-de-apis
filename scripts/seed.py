"""Popula o banco com o usuário administrador e dados de exemplo.

Uso (a partir da raiz do projeto, após `alembic upgrade head`):

    python -m scripts.seed                # administrador + dados de exemplo
    python -m scripts.seed --sem-exemplos # somente o administrador

O script é idempotente: pode ser executado várias vezes sem duplicar dados.
As credenciais do administrador vêm de ADMIN_USERNAME e ADMIN_PASSWORD (.env).
"""

import argparse
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import gerar_hash_senha
from app.db.session import SessionLocal
from app.models import Hospede, Quarto, Reserva, StatusReserva, TipoQuarto, Usuario


def criar_admin(db: Session) -> None:
    settings = get_settings()
    if not settings.admin_username or not settings.admin_password:
        print("[seed] ADMIN_USERNAME/ADMIN_PASSWORD não definidos no .env - administrador não criado.")
        return

    existente = db.scalar(select(Usuario).where(Usuario.username == settings.admin_username))
    if existente:
        print(f"[seed] Usuário '{settings.admin_username}' já existe.")
        return

    db.add(
        Usuario(
            username=settings.admin_username,
            senha_hash=gerar_hash_senha(settings.admin_password),
        )
    )
    print(f"[seed] Usuário administrador '{settings.admin_username}' criado.")


def criar_exemplos(db: Session) -> None:
    if db.scalar(select(Quarto.id).limit(1)) is not None:
        print("[seed] Já existem quartos cadastrados - dados de exemplo não inseridos.")
        return

    quartos = [
        Quarto(numero="101", tipo=TipoQuarto.SOLTEIRO, capacidade=1, preco_diaria=Decimal("180.00"), andar=1,
               descricao="Quarto individual com vista para o jardim."),
        Quarto(numero="102", tipo=TipoQuarto.CASAL, capacidade=2, preco_diaria=Decimal("260.00"), andar=1,
               descricao="Cama queen-size e varanda."),
        Quarto(numero="201", tipo=TipoQuarto.DUPLO, capacidade=2, preco_diaria=Decimal("240.00"), andar=2,
               descricao="Duas camas de solteiro."),
        Quarto(numero="202", tipo=TipoQuarto.CASAL, capacidade=3, preco_diaria=Decimal("300.00"), andar=2,
               descricao="Cama king-size e sofá-cama."),
        Quarto(numero="301", tipo=TipoQuarto.SUITE, capacidade=4, preco_diaria=Decimal("520.00"), andar=3,
               descricao="Suíte com hidromassagem e sala de estar."),
        Quarto(numero="302", tipo=TipoQuarto.SUITE, capacidade=4, preco_diaria=Decimal("480.00"), andar=3,
               descricao="Suíte em reforma.", ativo=False),
    ]
    hospedes = [
        Hospede(nome="Ana Carolina Souza", cpf="52601815906", email="ana.souza@example.com",
                telefone="41999990001", data_nascimento=date(1990, 3, 12)),
        Hospede(nome="Bruno Henrique Lima", cpf="08301661305", email="bruno.lima@example.com",
                telefone="11988880002", data_nascimento=date(1985, 7, 25)),
        Hospede(nome="Carla Mendes Rocha", cpf="18609139034", email="carla.rocha@example.com",
                telefone="21977770003"),
        Hospede(nome="Diego Ferreira Alves", cpf="99603082430", email="diego.alves@example.com"),
    ]
    db.add_all(quartos + hospedes)
    db.flush()  # obtém os IDs gerados antes de criar as reservas

    hoje = date.today()

    def nova_reserva(hospede: Hospede, quarto: Quarto, inicio_em_dias: int, diarias: int,
                     qtd: int, status: StatusReserva = StatusReserva.CONFIRMADA) -> Reserva:
        checkin = hoje + timedelta(days=inicio_em_dias)
        return Reserva(
            hospede_id=hospede.id,
            quarto_id=quarto.id,
            data_checkin=checkin,
            data_checkout=checkin + timedelta(days=diarias),
            qtd_hospedes=qtd,
            status=status,
            valor_total=quarto.preco_diaria * diarias,
        )

    db.add_all([
        nova_reserva(hospedes[0], quartos[1], inicio_em_dias=5, diarias=3, qtd=2),
        nova_reserva(hospedes[1], quartos[4], inicio_em_dias=10, diarias=4, qtd=3),
        nova_reserva(hospedes[2], quartos[0], inicio_em_dias=2, diarias=2, qtd=1, status=StatusReserva.CANCELADA),
    ])
    print(f"[seed] Inseridos {len(quartos)} quartos, {len(hospedes)} hóspedes e 3 reservas de exemplo.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Popula o banco da Hotel API.")
    parser.add_argument("--sem-exemplos", action="store_true", help="cria apenas o usuário administrador")
    args = parser.parse_args()

    with SessionLocal() as db:
        criar_admin(db)
        if not args.sem_exemplos:
            criar_exemplos(db)
        db.commit()


if __name__ == "__main__":
    main()
