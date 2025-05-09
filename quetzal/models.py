import os
import uuid
import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship

db = SQLAlchemy()

def get_uuid():
    """Generate a unique ID for records"""
    return str(uuid.uuid4())

class Folder(db.Model):
    """Folder model for organizing documents and chats"""
    __tablename__ = "folders"
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.String(36), db.ForeignKey('folders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    parent = relationship("Folder", remote_side=[id], backref="children")
    documents = relationship("Document", back_populates="folder")
    chats = relationship("Chat", back_populates="folder")
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "children": [child.to_dict() for child in self.children] if self.children else []
        }

class Document(db.Model):
    """Document model for files and URLs processed by the assistant"""
    __tablename__ = "documents"
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    title = db.Column(db.String(255), nullable=False)
    source = db.Column(db.String(1024), nullable=False)  # URL or file path
    vector_id = db.Column(db.String(36), nullable=True)  # ID in the vector store
    folder_id = db.Column(db.String(36), db.ForeignKey('folders.id'), nullable=True)
    document_type = db.Column(db.String(20), nullable=False)  # 'file', 'url', etc.
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    folder = relationship("Folder", back_populates="documents")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "source": self.source,
            "vector_id": self.vector_id,
            "folder_id": self.folder_id,
            "document_type": self.document_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Chat(db.Model):
    """Chat model for conversations with the assistant"""
    __tablename__ = "chats"
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    title = db.Column(db.String(255), nullable=False, default="New Chat")
    folder_id = db.Column(db.String(36), db.ForeignKey('folders.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    folder = relationship("Folder", back_populates="chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "folder_id": self.folder_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Message(db.Model):
    """Message model for individual messages in a chat"""
    __tablename__ = "messages"
    
    id = db.Column(db.String(36), primary_key=True, default=get_uuid)
    chat_id = db.Column(db.String(36), db.ForeignKey('chats.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    sources = db.Column(db.JSON, nullable=True)  # JSON array of source references
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    
    def to_dict(self):
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 