import re

from app.models import Ticket


class CategoryClassifier:
    """Derives issue category names dynamically from ticket summary text."""

    def classify(self, ticket: Ticket) -> str:
        return self._extract_from_summary(ticket.summary) or "Others"

    def _extract_from_summary(self, summary: str) -> str | None:
        text = summary.strip()
        if not text:
            return None

        dash_parts = [part.strip() for part in text.split(" - ") if part.strip()]
        if dash_parts and re.match(r"^CL\d+", dash_parts[0], re.IGNORECASE):
            if len(dash_parts) >= 4:
                return dash_parts[3]
            if len(dash_parts) == 3:
                return dash_parts[2]
            if len(dash_parts) == 2:
                return dash_parts[1]

        colon_match = re.match(r"^([^:]+:\s*[^:]+:\s*)(.+)$", text)
        if colon_match:
            return colon_match.group(2).strip()

        if len(dash_parts) >= 3:
            return dash_parts[2]

        if len(dash_parts) == 2:
            return dash_parts[1]

        return text
