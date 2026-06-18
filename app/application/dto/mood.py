from dataclasses import dataclass


@dataclass(frozen=True)
class MoodAnalysis:
    mood_score: int
    mood_label: str
    tags: list[str]
