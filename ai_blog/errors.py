class OpenAIAuthError(Exception):
    """Raised when OpenAI authentication fails."""


class OpenAIRateLimitError(Exception):
    """Raised when OpenAI rate limit or quota is exceeded."""


class MockDryRunRegressionError(Exception):
    """Raised when mock or dry-run output fails validation."""
