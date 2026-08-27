from datetime import datetime

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


# ============================================================
# EXPENSE
# ============================================================

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

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Lainnya",
    )

    # Tanggal transaksi dari struk
    expense_date: Mapped[datetime | None] = mapped_column(
        Date,
        nullable=True,
    )

    # Waktu data dimasukkan ke sistem
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relasi ke item
    items: Mapped[list["ExpenseItem"]] = relationship(
        "ExpenseItem",
        back_populates="expense",
        cascade="all, delete-orphan",
    )


# ============================================================
# EXPENSE ITEM
# ============================================================

class ExpenseItem(Base):

    __tablename__ = "expense_items"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    expense_id: Mapped[int] = mapped_column(
        ForeignKey(
            "expenses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    expense: Mapped["Expense"] = relationship(
        "Expense",
        back_populates="items",
    )