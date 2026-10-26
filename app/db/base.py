"""Base declarativa do SQLAlchemy.

Todas as classes de modelo herdam de `Base`; o SQLAlchemy usa os metadados
reunidos aqui para mapear cada classe para a sua tabela no banco. A convenção
de nomes deixa explícitos os nomes de índices e constraints, o que torna as
migrations do Alembic previsíveis.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCAO_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_NOMES)
