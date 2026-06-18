from abc import ABC, abstractmethod
from uuid import UUID

from app.domain.entities.user import User


class UserRepository(ABC):
    @abstractmethod
    def create_from_telegram(
        self,
        telegram_user_id: int,
        telegram_username: str | None,
        first_name: str | None,
        last_name: str | None,
        timezone: str,
    ) -> User:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: UUID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def update_telegram_profile(
        self,
        user_id: UUID,
        telegram_username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> User:
        raise NotImplementedError
