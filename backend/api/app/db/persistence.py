"""Persistence context that encapsulates transactional repositories."""
from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.prediccion_repository import PrediccionRepository
from app.db.session import async_session_factory


class PersistenceContext:
    """Manage the lifecycle of a database transaction and expose repositories."""

    def __init__(
        self,
        session_factory: Callable[[], AsyncSession] = async_session_factory,
    ) -> None:
        self._session_factory = session_factory
        self._session: AsyncSession | None = None
        self.predicciones: PrediccionRepository | None = None

    async def __aenter__(self) -> "PersistenceContext":
        self._session = self._session_factory()
        self.predicciones = PrediccionRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if self._session is None:
            return

        try:
            if exc:
                await self._session.rollback()
            else:
                await self._session.commit()
        finally:
            await self._session.close()

    @property
    def session(self) -> AsyncSession:
        if self._session is None:
            raise RuntimeError("PersistenceContext session not initialised; use within 'async with'.")
        return self._session

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()
