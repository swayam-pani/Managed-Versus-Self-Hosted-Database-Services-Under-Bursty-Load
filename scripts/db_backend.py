"""
db_backend.py
==============
Thin abstraction so every benchmark script (baseline, burst, sweep) can run
against either backend without duplicating connection logic.

Backends:
  --backend sqlite    -> local file testbed_db.sqlite (no external services
                          needed; this is what actually produced every
                          measured result in this repository so far).
  --backend postgres  -> the Dockerized PostgreSQL 15-alpine service defined
                          in docker/docker-compose.yml. Requires:
                              pip install psycopg2-binary
                              docker compose -f docker/docker-compose.yml up -d
                          NOTE: this backend has NOT been exercised in this
                          environment (no Docker/network access here). It is
                          provided so the project owner can run it on their
                          own machine and get a real, comparable managed-vs-
                          self-hosted-Postgres measurement. Until then, any
                          reference to "self-hosted PostgreSQL" results in
                          this repo's docs is corrected to say SQLite.
"""
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PATH = os.path.join(BASE_DIR, "testbed_db.sqlite")

# Automatically load .env if present
_env_file = os.path.join(BASE_DIR, ".env")
if os.path.exists(_env_file):
    try:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
    except Exception:
        pass

POSTGRES_DSN = dict(
    host=os.environ.get("PG_HOST", "localhost"),
    port=os.environ.get("PG_PORT", "5432"),
    dbname=os.environ.get("PG_DB", "db_testbed"),
    user=os.environ.get("PG_USER", "admin_user"),
    password=os.environ.get("PG_PASSWORD", "SecretPassword123!"),
)


class Backend:
    """Wraps a DB-API connection so callers use the same placeholder style
    and the same schema regardless of backend.
    
    Supported backends:
      - 'sqlite'
      - 'postgres', 'postgres_self_hosted', or 'postgres_docker' (Docker containerized)
      - 'postgres_managed' (Remote Cloud SQL / RDS / Serverless Neon AWS Ohio)
    """

    # Connection pooling configuration parameters
    DEFAULT_MIN_CONNECTIONS = 1
    DEFAULT_MAX_CONNECTIONS = 20
    DEFAULT_CONNECT_TIMEOUT = 10  # seconds

    def __init__(self, kind, max_connections=20, connect_timeout=10):
        self.kind = kind
        self.max_connections = max_connections
        self.connect_timeout = connect_timeout
        self.pool = None

        if kind == "sqlite":
            self.conn = sqlite3.connect(SQLITE_PATH)
            self.placeholder = "?"
        elif kind in ("postgres", "postgres_self_hosted", "postgres_docker"):
            try:
                import psycopg2
                from psycopg2 import pool
            except ImportError as e:
                raise SystemExit("psycopg2-binary is not installed.") from e
            dsn = dict(
                host=os.environ.get("SELFHOSTED_PG_HOST", os.environ.get("PG_HOST", "localhost")),
                port=os.environ.get("SELFHOSTED_PG_PORT", os.environ.get("PG_PORT", "5432")),
                dbname=os.environ.get("SELFHOSTED_PG_DB", os.environ.get("PG_DB", "db_testbed")),
                user=os.environ.get("SELFHOSTED_PG_USER", os.environ.get("PG_USER", "admin_user")),
                password=os.environ.get("SELFHOSTED_PG_PASSWORD", os.environ.get("PG_PASSWORD", "SecretPassword123!")),
                connect_timeout=self.connect_timeout,
            )
            try:
                self.pool = pool.ThreadedConnectionPool(
                    minconn=self.DEFAULT_MIN_CONNECTIONS,
                    maxconn=self.max_connections,
                    **dsn
                )
                self.conn = self.pool.getconn()
            except Exception:
                # Fallback to direct single connection if pooler/server has strict limits
                self.conn = psycopg2.connect(**dsn)
            self.conn.autocommit = False
            self.placeholder = "%s"
        elif kind == "postgres_managed":
            try:
                import psycopg2
                from psycopg2 import pool
            except ImportError as e:
                raise SystemExit("psycopg2-binary is not installed.") from e
            
            # Neon Managed PostgreSQL Endpoint on AWS Ohio (us-east-2) with Connection Pooling
            url = os.environ.get("MANAGED_PG_URL", os.environ.get("DATABASE_URL", None))
            if url:
                try:
                    self.pool = pool.ThreadedConnectionPool(
                        minconn=self.DEFAULT_MIN_CONNECTIONS,
                        maxconn=self.max_connections,
                        dsn=url,
                        connect_timeout=self.connect_timeout
                    )
                    self.conn = self.pool.getconn()
                except Exception:
                    self.conn = psycopg2.connect(url, connect_timeout=self.connect_timeout)
            else:
                dsn = dict(
                    host=os.environ.get("MANAGED_PG_HOST", "localhost"),
                    port=os.environ.get("MANAGED_PG_PORT", "5432"),
                    dbname=os.environ.get("MANAGED_PG_DB", "postgres"),
                    user=os.environ.get("MANAGED_PG_USER", "postgres"),
                    password=os.environ.get("MANAGED_PG_PASSWORD", ""),
                    sslmode=os.environ.get("MANAGED_PG_SSLMODE", "prefer"),
                    connect_timeout=self.connect_timeout,
                )
                try:
                    self.pool = pool.ThreadedConnectionPool(
                        minconn=self.DEFAULT_MIN_CONNECTIONS,
                        maxconn=self.max_connections,
                        **dsn
                    )
                    self.conn = self.pool.getconn()
                except Exception:
                    self.conn = psycopg2.connect(**dsn)
            self.conn.autocommit = False
            self.placeholder = "%s"
        else:
            raise ValueError(f"unknown backend: {kind}")

    def cursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def close(self):
        if hasattr(self, 'conn') and self.conn:
            try:
                self.conn.close()
            except Exception:
                pass
        if hasattr(self, 'pool') and self.pool:
            try:
                self.pool.closeall()
            except Exception:
                pass

    def q(self, sql_with_qmarks):
        """Rewrite a SQL string written with '?' placeholders into the
        correct placeholder style for this backend."""
        if self.placeholder == "?":
            return sql_with_qmarks
        return sql_with_qmarks.replace("?", "%s")

    def ensure_schema_and_seed(self, n_accounts=10000, log_fn=None):
        cur = self.cursor()
        if self.kind == "sqlite":
            cur.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_uuid TEXT UNIQUE,
                customer_name TEXT,
                balance REAL,
                status TEXT
            );""")
            cur.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                receiver_id INTEGER,
                amount REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );""")
            cur.execute("SELECT COUNT(*) FROM accounts;")
            count = cur.fetchone()[0]
            if count < n_accounts:
                import random
                if log_fn:
                    log_fn(f"Seeding {n_accounts} account records into SQLite...")
                seed = [
                    (f"acc-uuid-{i}", f"Customer_{i}",
                     round(random.uniform(100, 5000), 2), "ACTIVE")
                    for i in range(1, n_accounts + 1)
                ]
                cur.executemany(
                    "INSERT INTO accounts (account_uuid, customer_name, balance, status) "
                    "VALUES (?, ?, ?, ?);", seed)
                self.commit()
        else:
            # PostgreSQL backend (self-hosted or managed)
            # Check if accounts table exists
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'accounts'
                );
            """)
            exists = cur.fetchone()[0]
            if not exists:
                if log_fn:
                    log_fn(f"Initializing PostgreSQL schema on {self.kind}...")
                schema_path = os.path.join(BASE_DIR, "scripts", "init_schema.sql")
                with open(schema_path, "r") as f:
                    schema_sql = f.read()
                ddl_sql = "\n".join([line for line in schema_sql.splitlines() if not line.strip().upper().startswith("VACUUM")])
                cur.execute(ddl_sql)
                self.commit()
            
            cur.execute("SELECT COUNT(*) FROM accounts;")
            count = cur.fetchone()[0]
            if log_fn:
                log_fn(f"{self.kind} accounts table verified with {count} rows.")
        return cur
