from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from database.models import Base


# ============================================================
# DATABASE URL
# ============================================================

DATABASE_URL = (
    "sqlite:///database/expenses.db"
)


# ============================================================
# ENGINE
# ============================================================

engine = create_engine(

    DATABASE_URL,

    connect_args={
        "check_same_thread": False,
    },

)


# ============================================================
# SESSION
# ============================================================

SessionLocal = sessionmaker(

    bind=engine,

    autocommit=False,

    autoflush=False,

)


# ============================================================
# INIT DATABASE
# ============================================================

def init_db():

    Base.metadata.create_all(
        bind=engine
    )