class AIProviderError(Exception):
    """An AI provider call failed; status_code and detail are safe to show users."""

    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail
