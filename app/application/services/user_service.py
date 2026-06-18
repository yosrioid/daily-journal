from app.domain.entities.user import User
from app.domain.interfaces.user_repository import UserRepository


class UserService:
    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    def resolve_telegram_user(
        self,
        telegram_user_id: int,
        telegram_username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        timezone: str = "Asia/Jakarta",
    ) -> User:
        user = self.user_repository.get_by_telegram_user_id(telegram_user_id)
        if user is None:
            return self.user_repository.create_from_telegram(
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
                first_name=first_name,
                last_name=last_name,
                timezone=timezone,
            )

        if self._profile_changed(user, telegram_username, first_name, last_name):
            return self.user_repository.update_telegram_profile(
                user_id=user.id,
                telegram_username=telegram_username,
                first_name=first_name,
                last_name=last_name,
            )

        return user

    def _profile_changed(
        self,
        user: User,
        telegram_username: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> bool:
        return (
            user.telegram_username != telegram_username
            or user.first_name != first_name
            or user.last_name != last_name
        )
