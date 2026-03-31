# test_database_connection.py
#
# Run with:  python -m pytest test_database_connection.py -v
#
# Requires no real database — all driver calls are mocked.
# The goal is to prove the refactored code preserves every
# behaviour the original code guaranteed.

import pytest
import threading
from unittest.mock import MagicMock, patch, call
from abc import ABC

import refactored_fd
import connections      

# ══════════════════════════════════════════════════════════════════════════════
# Shared fixtures
# ══════════════════════════════════════════════════════════════════════════════

MYSQL_KWARGS = dict(
    host="localhost", port=3306,
    username="db_user", password="secret",
    database="app_db",
)

MONGO_KWARGS = dict(
    host="mongo.example.com", port=27017,
    username="mongo_user", password="mongo123",
    database="analytics",
    pool_size=10, retry_attempts=5,
)


@pytest.fixture(autouse=True)
def reset_pool():
    """Guarantee a fresh ConnectionPool singleton for every test."""
    connections.ConnectionPool._instance = None
    yield
    connections.ConnectionPool._instance = None


@pytest.fixture()
def event_bus():
    return connections.ConnectionEventBus()


@pytest.fixture()
def mock_mysql(monkeypatch):
    """Patch the MySQL driver so no real connection is attempted."""
    fake_conn = MagicMock(name="mysql_connection")
    monkeypatch.setattr(
        "db_connection.MySQLConnection._create_driver_connection",
        lambda self, url: fake_conn,
    )
    return fake_conn


# ══════════════════════════════════════════════════════════════════════════════
# 1. Factory — creation, registry, extensibility
# ══════════════════════════════════════════════════════════════════════════════

class TestFactory:
    """DatabaseConnectionFactory produces the correct concrete type."""

    @pytest.mark.parametrize("db_type, expected_class", [
        ("mysql",      refactored_fd.MySQLConnection),
        ("postgresql", refactored_fd.PostgreSQLConnection),
        ("mongodb",    refactored_fd.MongoDBConnection),
        ("redis",      refactored_fd.RedisConnection),
    ])
    def test_create_returns_correct_type(self, db_type, expected_class):
        conn = refactored_fd.DatabaseConnectionFactory.create(db_type, **MYSQL_KWARGS)
        assert isinstance(conn, expected_class)

    def test_create_is_case_insensitive(self):
        for variant in ("MySQL", "MYSQL", "mysql", "MySql"):
            conn = refactored_fd.DatabaseConnectionFactory.create(variant, **MYSQL_KWARGS)
            assert isinstance(conn, refactored_fd.MySQLConnection), f"Failed for variant: {variant}"

    def test_unsupported_type_raises_value_error(self):
        with pytest.raises(ValueError, match="cassandra"):
            refactored_fd.DatabaseConnectionFactory.create("cassandra", **MYSQL_KWARGS)

    def test_error_message_lists_supported_types(self):
        with pytest.raises(ValueError) as exc_info:
            refactored_fd.DatabaseConnectionFactory.create("oracle", **MYSQL_KWARGS)
        msg = str(exc_info.value).lower()
        for db in ("mysql", "postgresql", "mongodb", "redis"):
            assert db in msg

    def test_register_adds_new_type(self):
        class CassandraConnection(refactored_fd.DatabaseConnection):
            def _build_connection_string(self):
                return f"cassandra://{self.host}:{self.port}"

        refactored_fd.DatabaseConnectionFactory.register("cassandra", CassandraConnection)
        try:
            conn = refactored_fd.DatabaseConnectionFactory.create("cassandra", **MYSQL_KWARGS)
            assert isinstance(conn, CassandraConnection)
        finally:
            # Clean up so other tests aren't affected
            refactored_fd.DatabaseConnectionFactory._registry.pop("cassandra", None)

    def test_register_overrides_existing_type(self):
        """register() should replace, not accumulate."""
        original = refactored_fd.DatabaseConnectionFactory._registry.get("redis")
        class CustomRedis(refactored_fd.DatabaseConnection):
            def _build_connection_string(self):
                return "custom-redis://"

        refactored_fd.DatabaseConnectionFactory.register("redis", CustomRedis)
        try:
            conn = refactored_fd.DatabaseConnectionFactory.create("redis", **MYSQL_KWARGS)
            assert isinstance(conn, CustomRedis)
        finally:
            refactored_fd.DatabaseConnectionFactory._registry["redis"] = original # type: ignore

    def test_kwargs_forwarded_to_constructor(self):
        conn = refactored_fd.DatabaseConnectionFactory.create(
            "mysql", **MYSQL_KWARGS, use_ssl=True, connection_timeout=60
        )
        assert conn.use_ssl is True
        assert conn.connection_timeout == 60


# ══════════════════════════════════════════════════════════════════════════════
# 2. Connection strings — the core original behaviour
# ══════════════════════════════════════════════════════════════════════════════

class TestConnectionStrings:
    """
    The original connect() produced specific connection strings.
    These tests pin that contract precisely so the refactor can't silently
    break the format any driver depends on.
    """

    def test_mysql_basic_format(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        url = conn._build_connection_string()
        assert url.startswith("mysql://db_user:secret@localhost:3306/app_db")

    def test_mysql_includes_charset(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS, charset="latin1")  # type: ignore
        url = conn._build_connection_string()
        assert "charset=latin1" in url

    def test_mysql_default_charset_is_utf8(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        url = conn._build_connection_string()
        assert "charset=utf8" in url

    def test_mysql_includes_connection_timeout(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS, connection_timeout=45) # type: ignore
        url = conn._build_connection_string()
        assert "connectionTimeout=45" in url

    def test_mysql_ssl_appended_when_enabled(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS, use_ssl=True)  # type: ignore
        url = conn._build_connection_string()
        assert "useSSL=true" in url

    def test_mysql_no_ssl_param_when_disabled(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS, use_ssl=False) # type: ignore
        url = conn._build_connection_string()
        assert "useSSL" not in url

    def test_postgresql_basic_format(self):
        conn = refactored_fd.PostgreSQLConnection(**MYSQL_KWARGS)   # type: ignore
        url = conn._build_connection_string()
        assert url.startswith("postgresql://db_user:secret@localhost:3306/app_db")

    def test_postgresql_ssl_adds_sslmode(self):
        conn = refactored_fd.PostgreSQLConnection(**MYSQL_KWARGS, use_ssl=True) # type: ignore
        url = conn._build_connection_string()
        assert "sslmode=require" in url

    def test_postgresql_no_sslmode_when_disabled(self):
        conn = refactored_fd.PostgreSQLConnection(**MYSQL_KWARGS, use_ssl=False)    # type: ignore
        url = conn._build_connection_string()
        assert "sslmode" not in url

    def test_mongodb_basic_format(self):
        conn = refactored_fd.MongoDBConnection(**MONGO_KWARGS)  # type: ignore
        url = conn._build_connection_string()
        assert url.startswith("mongodb://mongo_user:mongo123@mongo.example.com:27017/analytics")

    def test_mongodb_includes_retry_attempts(self):
        conn = refactored_fd.MongoDBConnection(**MONGO_KWARGS)  # type: ignore
        url = conn._build_connection_string()
        assert "retryAttempts=5" in url

    def test_mongodb_includes_pool_size(self):
        conn = refactored_fd.MongoDBConnection(**MONGO_KWARGS)  # type: ignore
        url = conn._build_connection_string()
        assert "poolSize=10" in url

    def test_mongodb_ssl_flag(self):
        conn = refactored_fd.MongoDBConnection(**MONGO_KWARGS, use_ssl=True)    # type: ignore
        url = conn._build_connection_string()
        assert "ssl=true" in url

    def test_redis_basic_format(self):
        conn = refactored_fd.RedisConnection(**MYSQL_KWARGS)    # type: ignore
        url = conn._build_connection_string()
        assert "localhost" in url
        assert "3306" in url


# ══════════════════════════════════════════════════════════════════════════════
# 3. Abstract base class contract
# ══════════════════════════════════════════════════════════════════════════════

class TestAbstractBase:
    """DatabaseConnection enforces its abstract contract and shared behaviour."""

    def test_cannot_instantiate_abstract_class_directly(self):
        with pytest.raises(TypeError):
            refactored_fd.DatabaseConnection(**MYSQL_KWARGS)  # type: ignore

    def test_subclass_without_build_string_is_not_instantiable(self):
        class Incomplete(refactored_fd.DatabaseConnection):
            pass  # forgot to implement _build_connection_string

        with pytest.raises(TypeError):
            Incomplete(**MYSQL_KWARGS)  # type: ignore

    def test_config_stored_correctly_on_instance(self):
        conn = refactored_fd.MySQLConnection(
            host="h", port=1234, username="u", password="p",
            database="d", use_ssl=True, connection_timeout=99,
            retry_attempts=7, pool_size=3, charset="ascii",
        )
        assert conn.host == "h"
        assert conn.port == 1234
        assert conn.username == "u"
        assert conn.password == "p"
        assert conn.database == "d"
        assert conn.use_ssl is True
        assert conn.connection_timeout == 99
        assert conn.retry_attempts == 7
        assert conn.pool_size == 3
        assert conn.charset == "ascii"

    def test_connection_is_none_before_connect(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        assert conn.connection is None

    def test_execute_raises_when_not_connected(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        with pytest.raises(RuntimeError, match="connect"):
            conn.execute("SELECT 1")

    def test_disconnect_clears_connection(self, mock_mysql):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        conn.connect()
        assert conn.connection is not None
        conn.disconnect()
        assert conn.connection is None


# ══════════════════════════════════════════════════════════════════════════════
# 4. Default parameter values — preserved from original __init__
# ══════════════════════════════════════════════════════════════════════════════

class TestDefaults:
    """
    The original code had specific defaults. These must survive the refactor
    exactly — changing them silently is a breaking change for existing callers.
    """

    def test_use_ssl_defaults_false(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        assert conn.use_ssl is False

    def test_connection_timeout_defaults_30(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        assert conn.connection_timeout == 30

    def test_retry_attempts_defaults_3(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        assert conn.retry_attempts == 3

    def test_pool_size_defaults_5(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore      
        assert conn.pool_size == 5

    def test_charset_defaults_utf8(self):
        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        assert conn.charset == "utf8"


# ══════════════════════════════════════════════════════════════════════════════
# 5. Observer — subscribe, publish, ordering
# ══════════════════════════════════════════════════════════════════════════════

class TestObserver:

    def test_subscribed_callback_is_called_on_publish(self, event_bus):
        callback = MagicMock()
        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, callback)
        event_bus.publish(connections.ConnectionEvent.CONNECTED, host="localhost")
        callback.assert_called_once()

    def test_callback_receives_event_and_kwargs(self, event_bus):
        received = {}
        def capture(**kwargs):
            received.update(kwargs)

        event_bus.subscribe(connections.ConnectionEvent.CONNECTING, capture)
        event_bus.publish(connections.ConnectionEvent.CONNECTING, host="localhost", port=3306)

        assert received["event"] == connections.ConnectionEvent.CONNECTING
        assert received["host"] == "localhost"
        assert received["port"] == 3306

    def test_multiple_subscribers_all_called(self, event_bus):
        cb1, cb2, cb3 = MagicMock(), MagicMock(), MagicMock()
        for cb in (cb1, cb2, cb3):
            event_bus.subscribe(connections.ConnectionEvent.CONNECTED, cb)

        event_bus.publish(connections.ConnectionEvent.CONNECTED)
        cb1.assert_called_once()
        cb2.assert_called_once()
        cb3.assert_called_once()

    def test_subscribers_called_in_registration_order(self, event_bus):
        order = []
        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, lambda **kw: order.append(1))
        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, lambda **kw: order.append(2))
        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, lambda **kw: order.append(3))
        event_bus.publish(connections.ConnectionEvent.CONNECTED)
        assert order == [1, 2, 3]

    def test_callback_not_called_for_different_event(self, event_bus):
        callback = MagicMock()
        event_bus.subscribe(connections.ConnectionEvent.DISCONNECTED, callback)
        event_bus.publish(connections.ConnectionEvent.CONNECTED)
        callback.assert_not_called()

    def test_no_subscribers_publish_is_silent(self, event_bus):
        # Should not raise
        event_bus.publish(connections.ConnectionEvent.ERROR, reason="timeout")

    def test_unsubscribed_event_type_returns_empty(self, event_bus):
        event_bus.publish(connections.ConnectionEvent.RETRY)  # no subscriber — must not raise


# ══════════════════════════════════════════════════════════════════════════════
# 6. Observer resilience — a bad callback must never crash connect()
# ══════════════════════════════════════════════════════════════════════════════

class TestObserverResilience:

    def test_raising_callback_does_not_propagate(self, event_bus):
        def explode(**kwargs):
            raise RuntimeError("I am broken")

        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, explode)
        # publish should swallow the exception
        event_bus.publish(connections.ConnectionEvent.CONNECTED)  # must not raise

    def test_subsequent_callbacks_still_run_after_earlier_failure(self, event_bus):
        good_cb = MagicMock()

        def bad_cb(**kwargs):
            raise ValueError("bad")

        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, bad_cb)
        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, good_cb)
        event_bus.publish(connections.ConnectionEvent.CONNECTED)

        good_cb.assert_called_once()

    def test_broken_callback_is_logged_not_silenced(self, event_bus, caplog):
        import logging
        def explode(**kwargs):
            raise RuntimeError("callback failure")

        event_bus.subscribe(connections.ConnectionEvent.CONNECTED, explode)
        with caplog.at_level(logging.ERROR):
            event_bus.publish(connections.ConnectionEvent.CONNECTED)

        assert any("callback" in r.message.lower() or "observer" in r.message.lower()
                   for r in caplog.records)


# ══════════════════════════════════════════════════════════════════════════════
# 7. Event lifecycle — CONNECTING fires before CONNECTED
# ══════════════════════════════════════════════════════════════════════════════

class TestEventLifecycle:

    def test_connecting_fires_before_connected(self, mock_mysql):
        bus = connections.ConnectionEventBus()
        fired = []
        bus.subscribe(connections.ConnectionEvent.CONNECTING, lambda **kw: fired.append("CONNECTING"))
        bus.subscribe(connections.ConnectionEvent.CONNECTED,  lambda **kw: fired.append("CONNECTED"))

        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        conn._event_bus = bus   # type: ignore
        conn.connect()

        assert fired.index("CONNECTING") < fired.index("CONNECTED")

    def test_both_events_carry_host_information(self, mock_mysql):
        bus = connections.ConnectionEventBus()
        payloads = []
        for event in (connections.ConnectionEvent.CONNECTING, connections.ConnectionEvent.CONNECTED):
            bus.subscribe(event, lambda **kw: payloads.append(kw))

        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        conn._event_bus = bus   # type: ignore
        conn.connect()

        assert all("host" in p for p in payloads)
        assert all(p["host"] == "localhost" for p in payloads)

    def test_disconnected_event_fires_on_disconnect(self, mock_mysql):
        bus = connections.ConnectionEventBus()
        fired = MagicMock()
        bus.subscribe(connections.ConnectionEvent.DISCONNECTED, fired)

        conn = refactored_fd.MySQLConnection(**MYSQL_KWARGS)    # type: ignore
        conn._event_bus = bus   # type: ignore
        conn.connect()
        conn.disconnect()

        fired.assert_called_once()


# ══════════════════════════════════════════════════════════════════════════════
# 8. Connection pool — singleton, reuse, per-key isolation
# ══════════════════════════════════════════════════════════════════════════════

class TestConnectionPool:

    def test_pool_is_singleton(self):
        pool1 = connections.ConnectionPool()
        pool2 = connections.ConnectionPool()
        assert pool1 is pool2

    def test_same_key_returns_same_connection(self, mock_mysql):
        pool = connections.ConnectionPool()
        conn1 = pool.get_connection("mysql", **MYSQL_KWARGS)
        conn2 = pool.get_connection("mysql", **MYSQL_KWARGS)
        assert conn1 is conn2

    def test_different_databases_return_different_connections(self, monkeypatch):
        fake1 = MagicMock(name="conn_app")
        fake2 = MagicMock(name="conn_analytics")
        side_effects = [fake1, fake2]

        monkeypatch.setattr(
            "db_connection.MySQLConnection._create_driver_connection",
            lambda self, url: side_effects.pop(0),
        )

        pool = connections.ConnectionPool()
        conn1 = pool.get_connection("mysql", **{**MYSQL_KWARGS, "database": "app"})
        conn2 = pool.get_connection("mysql", **{**MYSQL_KWARGS, "database": "analytics"})
        assert conn1 is not conn2

    def test_dead_connection_is_replaced(self, mock_mysql):
        pool = connections.ConnectionPool()
        conn1 = pool.get_connection("mysql", **MYSQL_KWARGS)
        # Simulate the connection going dead
        conn1.connection = None
        conn2 = pool.get_connection("mysql", **MYSQL_KWARGS)
        # Pool should have reconnected — may be same object re-connected or new object
        assert conn2.connection is not None

    def test_pool_thread_safety(self, mock_mysql):
        """Two threads requesting the same key should get the same connection."""
        pool = connections.ConnectionPool()
        results = []

        def get():
            results.append(pool.get_connection("mysql", **MYSQL_KWARGS))

        threads = [threading.Thread(target=get) for _ in range(10)]
        for t in threads: t.start()
        for t in threads: t.join()

        assert len(set(id(r) for r in results)) == 1, \
            "All threads should receive the identical connection object"


# ══════════════════════════════════════════════════════════════════════════════
# 9. Builder — fluent API, validation, build()
# ══════════════════════════════════════════════════════════════════════════════

class TestBuilder:

    def _valid_builder(self):
        return (refactored_fd.DatabaseConnection.Builder("mysql")   # type: ignore
                .host("localhost", 3306)
                .credentials("user", "pass")
                .database("mydb"))

    def test_builder_produces_correct_type(self, mock_mysql):
        conn = self._valid_builder().build()
        assert isinstance(conn, refactored_fd.MySQLConnection)

    def test_builder_sets_host_and_port(self, mock_mysql):
        conn = self._valid_builder().build()
        assert conn.host == "localhost"
        assert conn.port == 3306

    def test_builder_sets_credentials(self, mock_mysql):
        conn = self._valid_builder().build()
        assert conn.username == "user"
        assert conn.password == "pass"

    def test_builder_sets_database(self, mock_mysql):
        conn = self._valid_builder().build()
        assert conn.database == "mydb"

    def test_with_ssl_sets_use_ssl_true(self, mock_mysql):
        conn = self._valid_builder().with_ssl().build()
        assert conn.use_ssl is True

    def test_without_ssl_leaves_use_ssl_false(self, mock_mysql):
        conn = self._valid_builder().build()
        assert conn.use_ssl is False

    def test_missing_host_raises_on_build(self):
        builder = (refactored_fd.DatabaseConnection.Builder("mysql")    # type: ignore
                   .credentials("user", "pass")
                   .database("mydb"))
        with pytest.raises(ValueError, match="host"):
            builder.build()

    def test_missing_credentials_raises_on_build(self):
        builder = (refactored_fd.DatabaseConnection.Builder("mysql")    # type: ignore
                   .host("localhost", 3306)
                   .database("mydb"))
        with pytest.raises(ValueError):
            builder.build()

    def test_missing_database_raises_on_build(self):
        builder = (refactored_fd.DatabaseConnection.Builder("mysql")    # type: ignore
                   .host("localhost", 3306)
                   .credentials("user", "pass"))
        with pytest.raises(ValueError, match="database"):
            builder.build()

    def test_builder_is_fluent(self, mock_mysql):
        """Each method must return self for chaining."""
        b = refactored_fd.DatabaseConnection.Builder("mysql")   # type: ignore
        assert b.host("h", 1) is b
        assert b.credentials("u", "p") is b
        assert b.database("d") is b
        assert b.with_ssl() is b


# ══════════════════════════════════════════════════════════════════════════════
# 10. Integration — end-to-end original usage patterns
# ══════════════════════════════════════════════════════════════════════════════

class TestIntegration:
    """
    Recreate the exact usage from the original code's example section.
    These are the highest-value tests: if they pass, the refactor is
    a drop-in replacement from the caller's perspective.
    """

    def test_original_mysql_usage_pattern(self, mock_mysql):
        """Mirrors the original mysql_db = DatabaseConnection(...) example."""
        conn = refactored_fd.DatabaseConnectionFactory.create(
            "mysql",
            host="localhost", port=3306,
            username="db_user", password="password123",
            database="app_db", use_ssl=True,
        )
        result = conn.connect()
        assert conn.connection is not None

    def test_original_mongodb_usage_pattern(self, monkeypatch):
        """Mirrors the original mongo_db = DatabaseConnection(...) example."""
        fake = MagicMock()
        monkeypatch.setattr(
            "db_connection.MongoDBConnection._create_driver_connection",
            lambda self, url: fake,
        )
        conn = refactored_fd.DatabaseConnectionFactory.create(
            "mongodb",
            host="mongodb.example.com", port=27017,
            username="mongo_user", password="mongo123",
            database="analytics", pool_size=10, retry_attempts=5,
        )
        conn.connect()
        url = conn._build_connection_string()
        assert "retryAttempts=5" in url
        assert "poolSize=10" in url

    def test_connect_then_execute_then_disconnect(self, mock_mysql):
        conn = refactored_fd.DatabaseConnectionFactory.create("mysql", **MYSQL_KWARGS)
        conn.connect()
        conn.execute("SELECT 1")            # must not raise
        conn.disconnect()
        assert conn.connection is None

    def test_execute_before_connect_raises(self):
        conn = refactored_fd.DatabaseConnectionFactory.create("mysql", **MYSQL_KWARGS)
        with pytest.raises(RuntimeError):
            conn.execute("SELECT 1")

    def test_factory_plus_observer_together(self, mock_mysql):
        """Factory, Strategy, and Observer all working in the same flow."""
        bus = connections.ConnectionEventBus()
        events_fired = []
        bus.subscribe(connections.ConnectionEvent.CONNECTING, lambda **kw: events_fired.append("CONNECTING"))
        bus.subscribe(connections.ConnectionEvent.CONNECTED,  lambda **kw: events_fired.append("CONNECTED"))

        conn = refactored_fd.DatabaseConnectionFactory.create("mysql", **MYSQL_KWARGS)
        conn._event_bus = bus   # type: ignore
        conn.connect()

        assert "CONNECTING" in events_fired
        assert "CONNECTED" in events_fired
        assert events_fired.index("CONNECTING") < events_fired.index("CONNECTED")

    def test_all_four_db_types_connect_without_error(self, monkeypatch):
        fake = MagicMock()
        for cls_name in ("MySQLConnection", "PostgreSQLConnection",
                         "MongoDBConnection", "RedisConnection"):
            monkeypatch.setattr(
                f"db_connection.{cls_name}._create_driver_connection",
                lambda self, url: fake,
            )

        for db_type in ("mysql", "postgresql", "mongodb", "redis"):
            conn = refactored_fd.DatabaseConnectionFactory.create(db_type, **MYSQL_KWARGS)
            conn.connect()  # must not raise