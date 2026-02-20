from sqlalchemy import Column, String, DateTime, Text, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class Connector(Base):
    __tablename__ = "connectors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)
    config = Column(JSONB, nullable=False)
    status = Column(String(20), default="inactive")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255))
    question = Column(Text, nullable=False)
    answer = Column(Text)
    sql_query = Column(Text)
    confidence = Column(Float)
    feedback = Column(String(20))
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MetadataTable(Base):
    __tablename__ = "metadata_tables"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connector_id = Column(UUID(as_uuid=True))
    schema_name = Column(String(255))
    table_name = Column(String(255), nullable=False)
    columns = Column(JSONB, nullable=False)
    row_count = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())