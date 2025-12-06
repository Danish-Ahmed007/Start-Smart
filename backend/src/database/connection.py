"""Database connection and ORM setup for Phase 1 backend.

Provides SQLAlchemy 2.0 engine, session factory, and base model class for ORM.
Supports both PostgreSQL (production) and SQLite (testing).
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.pool import NullPool, QueuePool

from ..utils.logger import Logger

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = Logger.get_logger(__name__)

# Create declarative base for ORM models
Base = declarative_base()


class DatabaseConnection:
    """
    Database connection manager with SQLAlchemy 2.0.
    
    Handles engine creation, connection pooling, and session management.
    Supports PostgreSQL and SQLite.
    """

    _instance: Optional[DatabaseConnection] = None
    _engine: Optional[Engine] = None
    _session_factory: Optional[sessionmaker] = None

    def __new__(cls) -> DatabaseConnection:
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize database connection (singleton)."""
        if self._initialized:
            return

        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Please configure in .env or system environment."
            )

        self.database_url = database_url
        self._initialize_engine()
        self._initialized = True
        logger.info(f"Database connection initialized: {self._get_db_type()}")

    def _get_db_type(self) -> str:
        """Detect database type from URL."""
        if "postgresql" in self.database_url or "postgres" in self.database_url:
            return "PostgreSQL"
        elif "sqlite" in self.database_url:
            return "SQLite"
        else:
            return "Unknown"

    def _initialize_engine(self) -> None:
        """Initialize SQLAlchemy engine with appropriate settings."""
        try:
            # Detect database type
            is_sqlite = "sqlite" in self.database_url.lower()

            # Configure pool based on database type
            if is_sqlite:
                # SQLite doesn't support concurrent connections well
                pool_config = {
                    "poolclass": NullPool,  # Don't pool SQLite connections
                    "connect_args": {"timeout": 15, "check_same_thread": False},
                }
                logger.debug("Using NullPool for SQLite")
            else:
                # PostgreSQL with connection pooling
                pool_config = {
                    "poolclass": QueuePool,
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_pre_ping": True,  # Verify connections before use
                    "pool_recycle": 3600,  # Recycle connections after 1 hour
                }
                logger.debug("Using QueuePool for PostgreSQL (pool_size=5, max_overflow=10)")

            # Create engine
            self._engine = create_engine(
                self.database_url,
                echo=os.getenv("SQL_ECHO", "false").lower() == "true",
                future=True,
                **pool_config,
            )

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine,
                class_=Session,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )

            # Test connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")

        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}", exc_info=True)
            raise

    @property
    def engine(self) -> Engine:
        """Get SQLAlchemy engine."""
        if self._engine is None:
            raise RuntimeError("Database engine not initialized")
        return self._engine

    @property
    def session_factory(self) -> sessionmaker:
        """Get SQLAlchemy session factory."""
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized")
        return self._session_factory

    def get_session(self) -> Session:
        """
        Get a new SQLAlchemy session.
        
        Note: Prefer using get_session_context() for context manager pattern.
        
        Returns:
            A new SQLAlchemy Session instance.
        """
        if self._session_factory is None:
            raise RuntimeError("Session factory not initialized")
        return self._session_factory()

    @contextmanager
    def get_session_context(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions.
        
        Automatically commits on success and rolls back on error.
        Ensures proper cleanup.
        
        Yields:
            A SQLAlchemy Session instance.
        
        Example:
            with db.get_session_context() as session:
                result = session.query(User).all()
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error, rolling back: {e}")
            raise
        finally:
            session.close()

    def create_all_tables(self) -> None:
        """
        Create all tables in the database.
        
        Uses metadata from ORM models (Base).
        Useful for testing and development initialization.
        
        Note: Use database migrations (Alembic) in production.
        """
        try:
            Base.metadata.create_all(self._engine)
            logger.info("All tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}", exc_info=True)
            raise

    def drop_all_tables(self) -> None:
        """
        Drop all tables from the database.
        
        WARNING: This will delete all data. Use only in testing.
        """
        try:
            Base.metadata.drop_all(self._engine)
            logger.warning("All tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}", exc_info=True)
            raise

    def get_table_names(self) -> list[str]:
        """
        Get list of all table names in the database.
        
        Returns:
            List of table names.
        """
        try:
            inspector = inspect(self._engine)
            return inspector.get_table_names()
        except Exception as e:
            logger.error(f"Failed to get table names: {e}", exc_info=True)
            return []

    def dispose_pool(self) -> None:
        """
        Dispose of the connection pool.
        
        Closes all connections and clears the pool.
        Useful for cleanup during shutdown.
        """
        try:
            if self._engine is not None:
                self._engine.dispose()
                logger.info("Connection pool disposed")
        except Exception as e:
            logger.error(f"Error disposing connection pool: {e}", exc_info=True)

    def ping(self) -> bool:
        """
        Test database connectivity.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database ping successful")
                return True
        except Exception as e:
            logger.error(f"Database ping failed: {e}")
            return False


# Global database instance
_db_instance: Optional[DatabaseConnection] = None


def get_db() -> DatabaseConnection:
    """
    Get or create the global database connection instance.
    
    Returns:
        The global DatabaseConnection singleton.
    
    Example:
        db = get_db()
        with db.get_session_context() as session:
            users = session.query(User).all()
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseConnection()
    return _db_instance


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Convenience function for getting a session context manager.
    
    Yields:
        A SQLAlchemy Session instance.
    
    Example:
        with get_session() as session:
            user = session.query(User).first()
    """
    db = get_db()
    with db.get_session_context() as session:
        yield session
