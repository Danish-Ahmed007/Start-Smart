"""Structured logging utility for StartSmart backend.

Provides configurable logging with:
- JSON formatting for production (log aggregation)
- Colorized console output for development
- Module-specific loggers
- Helper functions for API and database operation logging

Environment Variables:
- LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: INFO
- ENVIRONMENT: Deployment environment (development, production). Default: development
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class ColoredFormatter(logging.Formatter):
    """Formatter with color codes for console output in development."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        levelname = record.levelname
        color = self.COLORS.get(levelname, self.RESET)
        
        # Colorize the level name
        record.levelname = f"{color}{levelname}{self.RESET}"
        
        # Format the message
        formatted = super().format(record)
        
        # Restore original levelname (for next records)
        record.levelname = levelname
        
        return formatted


class JSONFormatter(logging.Formatter):
    """Formatter that outputs logs as JSON for production log aggregation."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_object = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if attached to record
        if hasattr(record, "extra_fields"):
            log_object.update(record.extra_fields)
        
        return json.dumps(log_object)


class Logger:
    """Logger factory providing configured loggers for the application.
    
    Implements singleton pattern to ensure consistent logging configuration
    across all modules.
    """

    _initialized: bool = False
    _environment: str = os.getenv("ENVIRONMENT", "development")
    _log_level: str = os.getenv("LOG_LEVEL", "INFO").upper()
    _loggers: Dict[str, logging.Logger] = {}

    @classmethod
    def _initialize(cls) -> None:
        """Initialize logging configuration (called once)."""
        if cls._initialized:
            return

        # Get logging level from environment
        level = getattr(logging, cls._log_level, logging.INFO)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        root_logger.handlers.clear()

        # Determine if production or development
        is_production = cls._environment.lower() == "production"

        if is_production:
            # Production: Use JSON formatter with file handler
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = JSONFormatter()
            handler.setFormatter(formatter)
        else:
            # Development: Use colored formatter with console handler
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(level)
            formatter = ColoredFormatter(
                fmt="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)

        root_logger.addHandler(handler)
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a logger for the given module name.

        Args:
            name: Module name, typically __name__

        Returns:
            Configured logger instance
            
        Example:
            >>> logger = Logger.get_logger(__name__)
            >>> logger.info("Application started")
        """
        cls._initialize()

        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger

        return cls._loggers[name]

    @classmethod
    def set_level(cls, level: str) -> None:
        """Change logging level at runtime.

        Args:
            level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        cls._initialize()
        numeric_level = getattr(logging, level.upper(), logging.INFO)
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)

    @classmethod
    def set_environment(cls, environment: str) -> None:
        """Change environment and reinitialize logging.

        Args:
            environment: Environment name (development, production)
        """
        cls._initialized = False
        cls._environment = environment
        cls._initialize()


def log_api_call(
    logger: logging.Logger,
    endpoint: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    status_code: Optional[int] = None,
    error: Optional[str] = None,
) -> None:
    """Log an API call with structured data.

    Args:
        logger: Logger instance
        endpoint: API endpoint path
        method: HTTP method (GET, POST, etc.)
        params: Request parameters/query string
        duration_ms: Request duration in milliseconds
        status_code: HTTP response status code
        error: Error message if request failed
        
    Example:
        >>> logger = Logger.get_logger(__name__)
        >>> log_api_call(
        ...     logger,
        ...     endpoint="/neighborhoods",
        ...     method="GET",
        ...     duration_ms=145.5,
        ...     status_code=200,
        ... )
    """
    extra_fields = {
        "api_endpoint": endpoint,
        "http_method": method,
    }

    if params:
        extra_fields["params"] = params

    if duration_ms is not None:
        extra_fields["duration_ms"] = round(duration_ms, 2)

    if status_code is not None:
        extra_fields["status_code"] = status_code

    if error:
        extra_fields["error"] = error
        level = logging.ERROR
        message = f"API call failed: {method} {endpoint}"
    else:
        level = logging.INFO
        message = f"API call completed: {method} {endpoint}"

    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname=logger.name,
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.extra_fields = extra_fields

    logger.handle(record)


def log_database_operation(
    logger: logging.Logger,
    operation: str,
    table: str,
    row_count: int = 0,
    duration_ms: Optional[float] = None,
    error: Optional[str] = None,
) -> None:
    """Log a database operation with structured data.

    Args:
        logger: Logger instance
        operation: Operation type (SELECT, INSERT, UPDATE, DELETE)
        table: Table name
        row_count: Number of rows affected
        duration_ms: Operation duration in milliseconds
        error: Error message if operation failed
        
    Example:
        >>> logger = Logger.get_logger(__name__)
        >>> log_database_operation(
        ...     logger,
        ...     operation="SELECT",
        ...     table="grid_cells",
        ...     row_count=42,
        ...     duration_ms=23.5,
        ... )
    """
    extra_fields = {
        "db_operation": operation,
        "table": table,
        "row_count": row_count,
    }

    if duration_ms is not None:
        extra_fields["duration_ms"] = round(duration_ms, 2)

    if error:
        extra_fields["error"] = error
        level = logging.ERROR
        message = f"Database operation failed: {operation} on {table}"
    else:
        level = logging.INFO
        message = f"Database operation: {operation} on {table} ({row_count} rows)"

    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname=logger.name,
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.extra_fields = extra_fields

    logger.handle(record)


def log_service_operation(
    logger: logging.Logger,
    operation: str,
    service: str,
    duration_ms: Optional[float] = None,
    result: Optional[Any] = None,
    error: Optional[str] = None,
) -> None:
    """Log a service operation with structured data.

    Args:
        logger: Logger instance
        operation: Operation name
        service: Service name
        duration_ms: Operation duration in milliseconds
        result: Result of operation (e.g., count, status)
        error: Error message if operation failed
        
    Example:
        >>> logger = Logger.get_logger(__name__)
        >>> log_service_operation(
        ...     logger,
        ...     operation="get_recommendations",
        ...     service="RecommendationService",
        ...     duration_ms=150.2,
        ...     result={"recommendations": 5},
        ... )
    """
    extra_fields = {
        "service": service,
        "operation": operation,
    }

    if duration_ms is not None:
        extra_fields["duration_ms"] = round(duration_ms, 2)

    if result is not None:
        extra_fields["result"] = result

    if error:
        extra_fields["error"] = error
        level = logging.ERROR
        message = f"Service operation failed: {service}.{operation}"
    else:
        level = logging.INFO
        message = f"Service operation: {service}.{operation}"

    record = logging.LogRecord(
        name=logger.name,
        level=level,
        pathname=logger.name,
        lineno=0,
        msg=message,
        args=(),
        exc_info=None,
    )
    record.extra_fields = extra_fields

    logger.handle(record)
