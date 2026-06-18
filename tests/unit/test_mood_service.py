from app.application.services.mood_service import MoodService


def test_mood_service_detects_positive_mood_and_tags() -> None:
    analysis = MoodService().analyze(
        "Today was produktif and I made progress learning Python #Backend",
    )

    assert analysis.mood_score > 5
    assert analysis.mood_label == "very_positive"
    assert analysis.tags == ["backend", "learning"]


def test_mood_service_detects_negative_mood() -> None:
    analysis = MoodService().analyze("I feel capek, stress, and overthinking.")

    assert analysis.mood_score < 5
    assert analysis.mood_label == "negative"


def test_mood_service_defaults_to_neutral() -> None:
    analysis = MoodService().analyze("I wrote a short note.")

    assert analysis.mood_score == 5
    assert analysis.mood_label == "neutral"
    assert analysis.tags == []
