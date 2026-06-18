import re

from app.application.dto.mood import MoodAnalysis

POSITIVE_WORDS = {
    "baik",
    "bagus",
    "happy",
    "produktif",
    "senang",
    "syukur",
    "grateful",
    "progress",
    "berhasil",
    "semangat",
    "calm",
    "tenang",
}
NEGATIVE_WORDS = {
    "buruk",
    "capek",
    "lelah",
    "sedih",
    "stress",
    "stres",
    "cemas",
    "anxious",
    "marah",
    "overthinking",
    "sakit",
    "gagal",
}
TOPIC_KEYWORDS = {
    "work": {"work", "kerja", "kantor", "project", "meeting", "deadline"},
    "learning": {"belajar", "learning", "python", "backend", "course", "study"},
    "health": {"sehat", "sakit", "health", "makan", "tidur", "sleep"},
    "finance": {"uang", "finance", "budget", "expense", "gaji", "bayar"},
    "family": {"family", "keluarga", "ayah", "ibu", "anak", "pasangan"},
    "fitness": {"gym", "workout", "lari", "olahraga", "exercise", "fitness"},
}


class MoodService:
    def analyze(self, raw_text: str) -> MoodAnalysis:
        words = self._words(raw_text)
        positive_count = sum(1 for word in words if word in POSITIVE_WORDS)
        negative_count = sum(1 for word in words if word in NEGATIVE_WORDS)
        score = self._score(positive_count, negative_count)

        return MoodAnalysis(
            mood_score=score,
            mood_label=self._label(score),
            tags=self._tags(raw_text, words),
        )

    def _score(self, positive_count: int, negative_count: int) -> int:
        score = 5 + (positive_count * 2) - (negative_count * 2)
        return max(1, min(10, score))

    def _label(self, score: int) -> str:
        if score <= 3:
            return "negative"
        if score <= 4:
            return "low"
        if score <= 6:
            return "neutral"
        if score <= 8:
            return "positive"
        return "very_positive"

    def _tags(self, raw_text: str, words: set[str]) -> list[str]:
        tags = self._hashtag_tags(raw_text)
        for tag, keywords in TOPIC_KEYWORDS.items():
            if words.intersection(keywords):
                tags.append(tag)

        return sorted(set(tags))

    def _hashtag_tags(self, raw_text: str) -> list[str]:
        return [
            match.group(1).lower()
            for match in re.finditer(r"#([A-Za-z0-9_]{2,32})", raw_text)
        ]

    def _words(self, raw_text: str) -> set[str]:
        return {
            match.group(0).lower()
            for match in re.finditer(r"[A-Za-zÀ-ÿ0-9_]+", raw_text)
        }
