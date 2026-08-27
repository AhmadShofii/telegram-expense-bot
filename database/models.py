from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)


class Base(DeclarativeBase):
    pass


class Expense(Base):

    __tablename__ = "expenses"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    description: Mapped[str] = (
        mapped_column(
            String(255),
            nullable=False,
        )
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    category: Mapped[str] = (
        mapped_column(
            String(100),
            nullable=False,
            default="Lainnya",
        )
    )

    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime,
            default=datetime.utcnow,
            nullable=False,
        )
    )