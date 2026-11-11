import urllib.parse
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import get_settings

settings = get_settings()

db_url = settings.DATABASE_URL

# Determine effective database connection and credentials
turso_url = settings.TURSO_DATABASE_URL or (settings.DATABASE_URL if ("turso.io" in settings.DATABASE_URL or settings.DATABASE_URL.startswith("libsql://")) else "")
is_turso = bool(turso_url)

if is_turso:
    try:
        import libsql_experimental
    except ImportError:
        raise ImportError(
            "libsql_experimental is required for Turso connections. "
            "Please install it via `pip install sqlalchemy-libsql` or `pip install libsql-experimental`."
        )

    parsed = urllib.parse.urlparse(turso_url)
    qs = urllib.parse.parse_qs(parsed.query)

    # Allow auth token from TURSO_AUTH_TOKEN or from query parameter (?authToken=...)
    auth_token = settings.TURSO_AUTH_TOKEN or qs.get("authToken", [""])[0]
    remote_host = parsed.netloc or parsed.path.lstrip("/")
    # Strip any trailing path or port details cleanly
    if "/" in remote_host:
        remote_host = remote_host.split("/")[0]

    turso_endpoint = f"https://{remote_host}"

    def libsql_creator():
        return libsql_experimental.connect(turso_endpoint, auth_token=auth_token)

    engine = create_engine("sqlite+libsql://", creator=libsql_creator, echo=False)

else:
    connect_args = {}
    if db_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        db_url,
        connect_args=connect_args,
        echo=False,
    )


# SQLite local file does not enforce foreign keys by default; enable PRAGMA foreign_keys=ON on connect
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if not is_turso and settings.DATABASE_URL.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency to provide a transactional database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


