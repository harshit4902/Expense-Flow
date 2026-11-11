import urllib.parse
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.config import get_settings

settings = get_settings()

db_url = settings.DATABASE_URL

# Handle Turso / LibSQL URLs seamlessly (e.g. libsql://... or sqlite+libsql://...)
if db_url.startswith("libsql://") or "turso.io" in db_url:
    try:
        import libsql_experimental
    except ImportError:
        raise ImportError(
            "libsql_experimental is required for Turso connections. "
            "Please install it via `pip install sqlalchemy-libsql` or `pip install libsql-experimental`."
        )

    parsed = urllib.parse.urlparse(db_url)
    qs = urllib.parse.parse_qs(parsed.query)
    auth_token = qs.get("authToken", [""])[0]
    remote_host = parsed.netloc
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
    if settings.DATABASE_URL.startswith("sqlite") and "turso.io" not in settings.DATABASE_URL:
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


