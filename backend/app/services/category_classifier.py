import json
from pathlib import Path

from app.models import Ticket


class CategoryClassifier:
    def __init__(self, rules_file: Path) -> None:
        self.rules_file = rules_file
        self.rules = self._load_rules()

    def classify(self, ticket: Ticket) -> str:
        searchable_text = " ".join(
            [
                ticket.summary,
                ticket.description,
                " ".join(ticket.labels),
                " ".join(ticket.components),
            ]
        ).lower()

        for category, keywords in self.rules.items():
            if any(keyword.lower() in searchable_text for keyword in keywords):
                return category
        return self._derive_from_summary(ticket.summary) or "Others"

    def _derive_from_summary(self, summary: str) -> str | None:
        parts = [part.strip() for part in summary.split(" - ") if part.strip()]
        if len(parts) >= 4 and parts[0].upper().startswith("CL"):
            return parts[3]
        if len(parts) >= 2 and parts[0].upper().startswith("CL"):
            return parts[-1]
        return None

    def _load_rules(self) -> dict[str, list[str]]:
        if not self.rules_file.exists():
            return {}

        with self.rules_file.open("r", encoding="utf-8") as file:
            rules = json.load(file)

        if not isinstance(rules, dict):
            raise ValueError("Alert Type rules must be a JSON object.")

        return {
            str(category): [str(keyword) for keyword in keywords]
            for category, keywords in rules.items()
            if isinstance(keywords, list)
        }
