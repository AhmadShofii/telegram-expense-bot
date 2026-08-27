from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


# ============================================================
# BASE
# ============================================================

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
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Lainnya",
    )

    description: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    expense_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        default=date.today,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

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
        Integer,
        ForeignKey(
            "expenses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
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
        default=0,
    )

    expense: Mapped["Expense"] = relationship(
        "Expense",
        back_populates="items",
    )


# ============================================================
# BUDGET
# ============================================================

class Budget(Base):

    __tablename__ = "budgets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    month: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )

    __table_args__ = (

        UniqueConstraint(
            "user_id",
            "year",
            "month",
            name="uq_budget_user_year_month",
        ),

    )


# ============================================================
# REMINDER
# ============================================================

class Reminder(Base):

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        unique=True,
        index=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    hour: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=20,
    )

    minute: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now,
    )