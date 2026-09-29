MAX_TEXT_CHARS = 200_000


class TextLimitError(ValueError):
    """Raised when submitted text is too large to scan."""


def ensure_text_limit(text: str) -> None:
    if len(text) > MAX_TEXT_CHARS:
        raise TextLimitError(f"text exceeds {MAX_TEXT_CHARS} characters")
