from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(String, unique=True, index=True)  # external uuid
    filename = Column(String, nullable=True)
    raw_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    chunks = relationship("ResumeChunk", back_populates="resume")


class ResumeChunk(Base):
    __tablename__ = "resume_chunks"
    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"))
    chunk_index = Column(Integer)
    text = Column(Text)

    resume = relationship("Resume", back_populates="chunks")


class Interview(Base):
    __tablename__ = "interviews"
    id = Column(Integer, primary_key=True, index=True)
    session_uuid = Column(String, unique=True, index=True)
    user_name = Column(String, nullable=True)
    resume_id = Column(Integer, ForeignKey("resumes.id"), nullable=True)
    status = Column(String, default="waiting")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    messages = relationship("Message", back_populates="interview")


class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    role = Column(String)  # AI or You
    text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    interview = relationship("Interview", back_populates="messages")


class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id"))
    technical = Column(Float, nullable=True)
    communication = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    completeness = Column(Float, nullable=True)
    relevance = Column(Float, nullable=True)
    reasoning = Column(Text, nullable=True)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    overall_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    data = Column(Text)


class Analytics(Base):
    __tablename__ = "analytics"
    id = Column(Integer, primary_key=True, index=True)
    interview_id = Column(Integer, ForeignKey("interviews.id"))
    metric = Column(String)
    value = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)
