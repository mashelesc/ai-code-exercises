from enum import Enum
from typing import Callable
import threading
from refactored_fd import DatabaseConnectionFactory, DatabaseConnection

class ConnectionEvent(Enum):
    CONNECTING   = "connecting"
    CONNECTED    = "connected"
    DISCONNECTED = "disconnected"
    ERROR        = "error"
    RETRY        = "retry"

class ConnectionEventBus:
    def __init__(self):
        self._listeners: dict[ConnectionEvent, list[Callable]] = {}

    def subscribe(self, event: ConnectionEvent, callback: Callable):
        self._listeners.setdefault(event, []).append(callback)

    def publish(self, event: ConnectionEvent, **data):
        for cb in self._listeners.get(event, []):
            cb(event=event, **data)

# Global bus — shared across the system
event_bus = ConnectionEventBus()

class ConnectionPool:
    _instance: "ConnectionPool | None" = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._pool: dict[str, DatabaseConnection] = {} # type: ignore
        return cls._instance

    def get_connection(self, db_type: str, **kwargs) -> DatabaseConnection:
        key = f"{db_type}:{kwargs['host']}:{kwargs['port']}/{kwargs['database']}"
        with self._lock:
            if key not in self._pool or not self._is_alive(key): # type: ignore
                conn = DatabaseConnectionFactory.create(db_type, **kwargs)
                conn.connect()
                self._pool[key] = conn # type: ignore
                event_bus.publish(ConnectionEvent.CONNECTED, key=key)
            return self._pool[key] # type: ignore

    def _is_alive(self, key: str) -> bool:
        return self._pool[key].connection is not None # type: ignore