class DailyJournalError(Exception):
    """Base exception for Daily Journal errors."""


class OwnershipError(DailyJournalError):
    """Raised when a user tries to access another user's data."""
