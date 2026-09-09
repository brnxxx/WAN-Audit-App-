from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # évite les connexions mortes après inactivité MySQL
    echo=False,           # passe à True temporairement si tu veux voir le SQL généré
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dependency FastAPI : ouvre une session, la ferme toujours après la requête."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()