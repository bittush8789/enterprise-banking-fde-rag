from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from backend.app.core.database import Base

# Association Table: user_roles
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
)

# Association Table: role_permissions
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
    Column("permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
)

# Association Table: document_permissions
document_permissions = Table(
    "document_permissions",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
)

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    users = relationship("User", secondary=user_roles, back_populates="roles")
    permissions = relationship("Permission", secondary=role_permissions, back_populates="roles")
    documents = relationship("Document", secondary=document_permissions, back_populates="allowed_roles")

class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(String(255), nullable=True)

    roles = relationship("Role", secondary=role_permissions, back_populates="permissions")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(150), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    roles = relationship("Role", secondary=user_roles, back_populates="users", lazy="joined")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_name = Column(String(255), nullable=False, index=True)
    document_type = Column(String(100), nullable=False)  # loan_policy, kyc_aml, product_guide, sop
    classification = Column(String(50), default="internal")  # public, internal, confidential, restricted
    department = Column(String(100), nullable=False)  # loan, compliance, retail, operations, it
    version = Column(String(50), default="v1.0")
    file_path = Column(String(500), nullable=False)
    status = Column(String(50), default="INDEXED")  # PENDING, INDEXING, INDEXED, FAILED
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    allowed_roles = relationship("Role", secondary=document_permissions, back_populates="documents", lazy="joined")

class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Chat", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string of structured citations
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    session = relationship("ChatSession", back_populates="messages")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    event_status = Column(String(50), nullable=False)  # SUCCESS, BLOCKED, FAILED, WARNING
    details = Column(Text, nullable=True)  # JSON string or masked text
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("User", back_populates="audit_logs")
