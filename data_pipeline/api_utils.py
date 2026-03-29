import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ── General HTTP settings ─────────────────────────────────────────────────────
REQUEST_TIMEOUT: int = 30       # seconds before a request is aborted
MAX_RETRIES: int = 3            # total attempts per request
RETRY_BACKOFF_BASE: int = 10    # base backoff in seconds; multiplied by attempt number


def _http_get(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    auth: tuple[str, str] | None = None,
    max_retries: int = MAX_RETRIES,
    backoff_base: int = RETRY_BACKOFF_BASE,
) -> requests.Response:
    """
    Perform an HTTP GET with retry logic and exponential backoff.

    Handles the following transient conditions automatically:
        - HTTP 429 Too Many Requests  → back off and retry
        - Network timeouts            → back off and retry
        - Connection errors           → back off and retry

    Non-transient HTTP errors (4xx except 429, 5xx) are raised immediately
    via ``raise_for_status()`` so callers know the request will not succeed.

    Args:
        url:          Target URL.
        params:       Query-string parameters dict.
        headers:      Additional HTTP request headers.
        auth:         (username, password) tuple for HTTP Basic Auth.
        max_retries:  Maximum number of attempts before raising.
        backoff_base: Seconds to wait on the first retry; multiplied by attempt.

    Returns:
        A successful ``requests.Response`` object.

    Raises:
        requests.HTTPError: On non-retryable HTTP error responses.
        RuntimeError:       When all retry attempts are exhausted.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                auth=auth,
                timeout=REQUEST_TIMEOUT,
            )

            # ── Rate-limit response: back off and retry ───────────────────
            if response.status_code == 429:
                wait = backoff_base * attempt
                logger.warning(
                    "HTTP 429 Too Many Requests (attempt %d/%d). "
                    "Sleeping %d s before retry …",
                    attempt, max_retries, wait,
                )
                time.sleep(wait)
                continue

            # ── All other non-2xx responses raise immediately ─────────────
            response.raise_for_status()
            return response

        except requests.exceptions.Timeout:
            wait = backoff_base * attempt
            logger.warning(
                "Request timed out (attempt %d/%d). URL: %s. "
                "Retrying in %d s …",
                attempt, max_retries, url, wait,
            )
            if attempt < max_retries:
                time.sleep(wait)

        except requests.exceptions.ConnectionError as exc:
            wait = backoff_base * attempt
            logger.warning(
                "Connection error (attempt %d/%d): %s. "
                "Retrying in %d s …",
                attempt, max_retries, exc, wait,
            )
            if attempt < max_retries:
                time.sleep(wait)

        except requests.exceptions.HTTPError:
            # Non-retryable; let it propagate to the caller.
            raise

    raise RuntimeError(
        f"All {max_retries} attempt(s) failed for URL: {url}"
    )
