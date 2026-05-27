"""데이터베이스 연결 및 세션 관리 모듈"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./bonus_score.db")

# SQLite의 경우 connect_args 필요
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # SQL 로그 출력 (개발 시 True)
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI Dependency: DB 세션 생성 및 반환"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
