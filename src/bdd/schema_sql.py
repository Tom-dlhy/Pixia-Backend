# src/db/schemas_sql.py
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, TIMESTAMP, JSON, ForeignKey, Enum, text
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()

class DocumentType(str, enum.Enum):
    COURSE = "course"
    EXERCISE = "exercise"
    EVAL = "eval"

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "public"}

    google_sub = Column(Text, primary_key=True)
    email = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    given_name = Column(Text)
    family_name = Column(Text)
    picture = Column(Text)
    locale = Column(Text)
    notion = Column(Text)
    drive = Column(Text)
    niveau_etudes = Column(Text)

    documents = relationship("Document", back_populates="user")

class DeepCourse(Base):
    __tablename__ = "deepcourse"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    titre = Column(Text, nullable=False)
    google_sub = Column(Text, ForeignKey("public.users.google_sub", ondelete="CASCADE"))

class Chapter(Base):
    __tablename__ = "chapter"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    deep_course_id = Column(Integer, ForeignKey("public.deepcourse.id", ondelete="CASCADE"))
    titre = Column(Text, nullable=False)
    is_complete = Column(Boolean, nullable=False, default=False)

    deep_course = relationship("DeepCourse")

class Document(Base):
    __tablename__ = "document"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True, autoincrement=True)
    google_sub = Column(Text, ForeignKey("public.users.google_sub", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(128), nullable=False)
    chapter_id = Column(Integer, ForeignKey("public.chapter.id", ondelete="CASCADE"), nullable=False)
    document_type = Column(Enum(DocumentType, name="document_type_enum"), nullable=False)
    contenu = Column(JSON, nullable=False)
    created_at = Column(TIMESTAMP, server_default=text("now()"))
    updated_at = Column(TIMESTAMP, server_default=text("now()"), onupdate=text("now()"))

    user = relationship("User", back_populates="documents")
    chapter = relationship("Chapter")

class SessionTitle(Base):
    __tablename__ = "session_titles"
    __table_args__ = {"schema": "public"}

    session_id = Column(String(128), primary_key=True)
    title = Column(Text, nullable=False)
    is_deepcourse = Column(Boolean, nullable=False, default=False)
