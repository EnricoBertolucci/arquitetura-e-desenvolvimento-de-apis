"""cria tabelas iniciais

Cria as tabelas quartos, hospedes, reservas e usuarios, com chaves
estrangeiras, constraints de unicidade/CHECK e índices de consulta.
Os CHECK dos campos enumerados (tipo, status) são gerados pelas próprias
colunas sa.Enum(create_constraint=True).

Revision ID: c9e7b86fe880
Revises: 
Create Date: 2026-10-15 15:50:09.745045

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# Identificadores da revisão, usados pelo Alembic.
revision: str = 'c9e7b86fe880'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Cria a estrutura inicial do banco."""
    op.create_table('hospedes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('nome', sa.String(length=120), nullable=False),
    sa.Column('cpf', sa.String(length=11), nullable=False),
    sa.Column('email', sa.String(length=254), nullable=False),
    sa.Column('telefone', sa.String(length=11), nullable=True),
    sa.Column('data_nascimento', sa.Date(), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_hospedes')),
    sa.UniqueConstraint('cpf', name=op.f('uq_hospedes_cpf')),
    sa.UniqueConstraint('email', name=op.f('uq_hospedes_email'))
    )
    op.create_table('quartos',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('numero', sa.String(length=10), nullable=False),
    sa.Column('tipo', sa.Enum('SOLTEIRO', 'CASAL', 'DUPLO', 'SUITE', name='tipo', native_enum=False, create_constraint=True, length=20), nullable=False),
    sa.Column('capacidade', sa.Integer(), nullable=False),
    sa.Column('preco_diaria', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('andar', sa.Integer(), nullable=False),
    sa.Column('descricao', sa.String(length=500), nullable=True),
    sa.Column('ativo', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('andar >= 0', name=op.f('ck_quartos_andar_nao_negativo')),
    sa.CheckConstraint('capacidade BETWEEN 1 AND 10', name=op.f('ck_quartos_capacidade_valida')),
    sa.CheckConstraint('preco_diaria > 0', name=op.f('ck_quartos_preco_diaria_positivo')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_quartos')),
    sa.UniqueConstraint('numero', name=op.f('uq_quartos_numero'))
    )
    op.create_table('usuarios',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=50), nullable=False),
    sa.Column('senha_hash', sa.String(length=255), nullable=False),
    sa.Column('ativo', sa.Boolean(), server_default=sa.text('1'), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_usuarios')),
    sa.UniqueConstraint('username', name=op.f('uq_usuarios_username'))
    )
    op.create_table('reservas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('hospede_id', sa.Integer(), nullable=False),
    sa.Column('quarto_id', sa.Integer(), nullable=False),
    sa.Column('data_checkin', sa.Date(), nullable=False),
    sa.Column('data_checkout', sa.Date(), nullable=False),
    sa.Column('qtd_hospedes', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('CONFIRMADA', 'CANCELADA', 'CONCLUIDA', name='status', native_enum=False, create_constraint=True, length=20), server_default='CONFIRMADA', nullable=False),
    sa.Column('valor_total', sa.Numeric(precision=10, scale=2), nullable=False),
    sa.Column('observacoes', sa.String(length=500), nullable=True),
    sa.Column('atualizado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.CheckConstraint('data_checkout > data_checkin', name=op.f('ck_reservas_periodo_valido')),
    sa.CheckConstraint('qtd_hospedes >= 1', name=op.f('ck_reservas_qtd_hospedes_positiva')),
    sa.CheckConstraint('valor_total >= 0', name=op.f('ck_reservas_valor_total_nao_negativo')),
    sa.ForeignKeyConstraint(['hospede_id'], ['hospedes.id'], name=op.f('fk_reservas_hospede_id_hospedes'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['quarto_id'], ['quartos.id'], name=op.f('fk_reservas_quarto_id_quartos'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_reservas'))
    )
    with op.batch_alter_table('reservas', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reservas_hospede_id'), ['hospede_id'], unique=False)
        batch_op.create_index('ix_reservas_quarto_periodo', ['quarto_id', 'data_checkin', 'data_checkout'], unique=False)
        batch_op.create_index(batch_op.f('ix_reservas_status'), ['status'], unique=False)



def downgrade() -> None:
    """Remove a estrutura inicial (ordem inversa por causa das FKs)."""
    with op.batch_alter_table('reservas', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reservas_status'))
        batch_op.drop_index('ix_reservas_quarto_periodo')
        batch_op.drop_index(batch_op.f('ix_reservas_hospede_id'))

    op.drop_table('reservas')
    op.drop_table('usuarios')
    op.drop_table('quartos')
    op.drop_table('hospedes')
