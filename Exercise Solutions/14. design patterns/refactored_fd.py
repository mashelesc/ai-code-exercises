from abc import ABC, abstractmethod


# ── Abstract base class ────────────────────────────────────────────────────────

class DatabaseConnection(ABC):
    def __init__(self, host, port, username, password, database,
                 use_ssl=False, connection_timeout=30, retry_attempts=3,
                 pool_size=5, charset='utf8'):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        self.use_ssl = use_ssl
        self.connection_timeout = connection_timeout
        self.retry_attempts = retry_attempts
        self.pool_size = pool_size
        self.charset = charset
        self.connection = None

    @abstractmethod
    def _build_connection_string(self) -> str:
        """Each subclass knows how to build its own connection string."""
        pass

    def connect(self):
        conn_string = self._build_connection_string()
        print(f"Connecting: {conn_string}")
        # In a real app: self.connection = <driver>.connect(conn_string)
        print("Connection successful!")
        return self.connection

    def disconnect(self):
        if self.connection:
            self.connection = None
            print("Disconnected.")

    def execute(self, query: str):
        if not self.connection:
            raise RuntimeError("Not connected. Call connect() first.")
        print(f"Executing: {query}")


# ── Concrete implementations ───────────────────────────────────────────────────

class MySQLConnection(DatabaseConnection):
    def _build_connection_string(self) -> str:
        url = (f"mysql://{self.username}:{self.password}"
               f"@{self.host}:{self.port}/{self.database}"
               f"?charset={self.charset}"
               f"&connectionTimeout={self.connection_timeout}")
        if self.use_ssl:
            url += "&useSSL=true"
        return url


class PostgreSQLConnection(DatabaseConnection):
    def _build_connection_string(self) -> str:
        url = (f"postgresql://{self.username}:{self.password}"
               f"@{self.host}:{self.port}/{self.database}")
        if self.use_ssl:
            url += "?sslmode=require"
        return url


class MongoDBConnection(DatabaseConnection):
    def _build_connection_string(self) -> str:
        url = (f"mongodb://{self.username}:{self.password}"
               f"@{self.host}:{self.port}/{self.database}"
               f"?retryAttempts={self.retry_attempts}"
               f"&poolSize={self.pool_size}")
        if self.use_ssl:
            url += "&ssl=true"
        return url


class RedisConnection(DatabaseConnection):
    def _build_connection_string(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.database}"


# ── Factory ────────────────────────────────────────────────────────────────────

class DatabaseConnectionFactory:
    _registry: dict[str, type[DatabaseConnection]] = {
        'mysql':      MySQLConnection,
        'postgresql': PostgreSQLConnection,
        'mongodb':    MongoDBConnection,
        'redis':      RedisConnection,
    }

    @classmethod
    def create(cls, db_type: str, **kwargs) -> DatabaseConnection:
        connector_class = cls._registry.get(db_type.lower())
        if not connector_class:
            supported = ', '.join(cls._registry)
            raise ValueError(
                f"Unsupported database type '{db_type}'. "
                f"Supported types: {supported}"
            )
        return connector_class(**kwargs)

    @classmethod
    def register(cls, db_type: str, connector_class: type[DatabaseConnection]):
        """Extend the factory at runtime without touching existing code."""
        cls._registry[db_type.lower()] = connector_class


# ── Usage ──────────────────────────────────────────────────────────────────────

mysql_db = DatabaseConnectionFactory.create(
    'mysql',
    host='localhost', port=3306,
    username='db_user', password='password123',
    database='app_db', use_ssl=True
)
mysql_db.connect()

mongo_db = DatabaseConnectionFactory.create(
    'mongodb',
    host='mongodb.example.com', port=27017,
    username='mongo_user', password='mongo123',
    database='analytics', pool_size=10, retry_attempts=5
)
mongo_db.connect()