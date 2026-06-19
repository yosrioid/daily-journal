from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepository
from app.infrastructure.database.models import UserModel
from app.shared.exceptions import NotFoundError


class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create_from_telegram(
        self,
        telegram_user_id: int,
        telegram_username: str | None,
        first_name: str | None,
        last_name: str | None,
        timezone: str,
    ) -> User:
        model = UserModel(
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            first_name=first_name,
            last_name=last_name,
            timezone=timezone,
        )
        self.session.add(model)
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def get_by_id(self, user_id: UUID) -> User | None:
        model = self.session.get(UserModel, user_id)
        return self._to_entity(model) if model is not None else None

    def get_by_telegram_user_id(self, telegram_user_id: int) -> User | None:
        statement = select(UserModel).where(
            UserModel.telegram_user_id == telegram_user_id,
        )
        model = self.session.scalar(statement)
        return self._to_entity(model) if model is not None else None

    def update_telegram_profile(
        self,
        user_id: UUID,
        telegram_username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> User:
        model = self.session.get(UserModel, user_id)
        if model is None:
            raise NotFoundError("User not found")

        model.telegram_username = telegram_username
        model.first_name = first_name
        model.last_name = last_name
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def update_timezone(self, user_id: UUID, timezone: str) -> User:
        model = self.session.get(UserModel, user_id)
        if model is None:
            raise NotFoundError("User not found")

        model.timezone = timezone
        self.session.flush()
        self.session.refresh(model)
        return self._to_entity(model)

    def _to_entity(self, model: UserModel) -> User:
        return User(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            telegram_username=model.telegram_username,
            first_name=model.first_name,
            last_name=model.last_name,
            timezone=model.timezone,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
