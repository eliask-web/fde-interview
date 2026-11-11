"""Shared retry policy for network tools: 3 attempts, exponential backoff."""

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

MAX_ATTEMPTS = 3


class FetchError(Exception):
    """A network call returned something unusable. Retried."""


retrying = retry(
    stop=stop_after_attempt(MAX_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type((FetchError, requests.RequestException)),
    reraise=True,
)
