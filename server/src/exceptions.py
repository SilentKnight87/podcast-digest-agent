"""Custom exception hierarchy for the Podcast Digest Agent."""


class PodcastDigestError(Exception):
    """Base exception for all application errors."""


class InvalidDataError(PodcastDigestError):
    """Raised when input data is invalid."""


class ServiceUnavailableError(PodcastDigestError):
    """Raised when a service dependency is unavailable."""


class InternalServerError(PodcastDigestError):
    """Raised when an unexpected error occurs."""
