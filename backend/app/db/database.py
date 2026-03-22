"""
Configuración y gestión de la base de datos SQLite.
Usa SQLAlchemy async con aiosqlite para operaciones no bloqueantes.
La base de datos se crea automáticamente al arrancar.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Motor de base de datos async
# check_same_thread=False es necesario para SQLite con múltiples tareas async
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Cambia a True para ver SQL en consola durante debugging
    connect_args={"check_same_thread": False},
)

# Fábrica de sesiones async
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Clase base para todos los modelos SQLAlchemy."""
    pass


async def inicializar_base_de_datos() -> None:
    """
    Crea todas las tablas definidas en los modelos si no existen.
    Se llama automáticamente al arrancar la aplicación.
    No requiere migraciones manuales para uso local.
    """
    # Importar modelos para que SQLAlchemy los registre
    from app.models import producto, cotizacion  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Tablas SQLite verificadas/creadas correctamente.")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection de FastAPI para obtener sesión de base de datos.
    Uso: async def mi_endpoint(db: AsyncSession = Depends(get_db))
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
