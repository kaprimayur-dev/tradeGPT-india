import os
import time
import logging
from typing import Optional, Dict, Any
import google.generativeai as genai
from google.api_core import exceptions

logger = logging.getLogger("GeminiClient")

# Hard internal safety ceilings
MAX_ALLOWED_DEADLINE_SECS: float = 30.0
MAX_ALLOWED_RETRIES: int = 2
DEFAULT_PER_CALL_TIMEOUT: float = 15.0

class GeminiClientError(Exception):
    """Base exception for all Gemini integration errors."""
    def __init__(self, message: str, status_code: int = 500, is_transient: bool = False):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.is_transient = is_transient

class GeminiAuthError(GeminiClientError):
    """Raised when the API key is missing or invalid (non-transient)."""
    def __init__(self, message: str = "Gemini API key is missing or invalid."):
        super().__init__(message, status_code=503, is_transient=False)

class GeminiRateLimitError(GeminiClientError):
    """Raised when rate limits (429) are exhausted."""
    def __init__(self, message: str = "Gemini API rate limit exceeded."):
        super().__init__(message, status_code=429, is_transient=True)

class GeminiTimeoutError(GeminiClientError):
    """Raised when the request exceeds the total allowed deadline or per-call transport timeout."""
    def __init__(self, message: str = "Gemini API request timed out."):
        super().__init__(message, status_code=504, is_transient=True)

class GeminiServiceUnavailableError(GeminiClientError):
    """Raised when Gemini returns 5xx (500, 502, 503, 504) or server is unavailable."""
    def __init__(self, message: str = "Gemini API service temporarily unavailable."):
        super().__init__(message, status_code=503, is_transient=True)


def get_default_model_name() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def call_gemini(
    prompt: str,
    model_name: Optional[str] = None,
    generation_config: Optional[Dict[str, Any]] = None,
    total_deadline_secs: float = 30.0,
    max_retries: int = 2,
    log: Optional[logging.Logger] = None
) -> str:
    """Invokes Google Gemini with a bounded total deadline, limited retries for transient errors only,
    genuine provider-level transport network timeout enforcement, and zero worker thread leakage.
    
    Hard Internal Safeguards (TG-002.12):
    - Elapsed time is measured using monotonic clocks (`time.monotonic()`).
    - Total deadline is hard-capped internally at 30.0 seconds; callers cannot increase it.
    - Max retries is hard-capped internally at 2 retries (at most 3 attempts total); callers cannot increase it.
    - Remaining deadline is recalculated immediately after each failed request.
    - Retry backoff sleep is strictly bounded and will abort immediately if insufficient budget remains.
    - Explicit `except GeminiClientError: raise` prevents custom exceptions from being reclassified.
    - Transient 5xx server and gateway errors (500, 502, 503, 504) are unified into GeminiServiceUnavailableError.
    
    Args:
        prompt: The text prompt to pass to Gemini.
        model_name: Model ID (defaults to GEMINI_MODEL env or gemini-2.5-flash).
        generation_config: Optional config dict (e.g. response_mime_type).
        total_deadline_secs: Requested ceiling on time spent (hard-capped internally at 30.0s).
        max_retries: Requested retries (hard-capped internally at 2 retries).
        log: Optional logger.
        
    Returns:
        The generated text string from Gemini.
        
    Raises:
        GeminiAuthError: Missing API key or invalid auth (never retried).
        GeminiRateLimitError: 429 quota exhaustion.
        GeminiTimeoutError: Total deadline expired or provider socket timeout.
        GeminiServiceUnavailableError: 5xx provider / gateway error.
        GeminiClientError: Any other error.
    """
    _log = log or logger
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        _log.error("GEMINI_API_KEY is not configured.")
        raise GeminiAuthError("Gemini API key is not configured in environment.")

    # Enforce internal safety ceilings: callers cannot increase these limits
    effective_deadline: float = min(max(float(total_deadline_secs), 0.001), MAX_ALLOWED_DEADLINE_SECS)
    effective_max_retries: int = min(max(int(max_retries), 0), MAX_ALLOWED_RETRIES)

    genai.configure(api_key=api_key)
    target_model = model_name or get_default_model_name()
    model = genai.GenerativeModel(target_model)

    start_time = time.monotonic()
    attempt = 0

    while True:
        attempt += 1
        elapsed = time.monotonic() - start_time
        remaining = effective_deadline - elapsed

        if attempt > 1 and remaining <= 0.5:
            _log.error(f"Gemini call timed out after {elapsed:.2f}s across {attempt-1} attempts.")
            raise GeminiTimeoutError(f"Gemini API total deadline ({effective_deadline}s) exceeded.")

        if remaining <= 0.0:
            _log.error(f"Gemini call timed out after {elapsed:.2f}s across {attempt-1} attempts.")
            raise GeminiTimeoutError(f"Gemini API total deadline ({effective_deadline}s) exceeded.")

        # Per-attempt socket deadline is minimum of remaining budget and DEFAULT_PER_CALL_TIMEOUT (15s)
        per_call_timeout = max(min(remaining, DEFAULT_PER_CALL_TIMEOUT), 0.001)

        try:
            _log.info(
                f"Invoking Gemini ({target_model}) [Attempt {attempt}/{effective_max_retries + 1}, "
                f"budget: {remaining:.1f}s, socket timeout: {per_call_timeout:.1f}s]"
            )
            
            # Configure native provider transport timeout and disable SDK's hidden internal retry
            kwargs: Dict[str, Any] = {
                "request_options": {
                    "timeout": per_call_timeout,
                    "retry": None
                }
            }
            if generation_config:
                kwargs["generation_config"] = generation_config

            response = model.generate_content(prompt, **kwargs)

            # Check if total deadline was exceeded while call was in-flight (or response arrived late)
            post_call_elapsed = time.monotonic() - start_time
            if post_call_elapsed > effective_deadline:
                _log.warning(f"Gemini response arrived after total deadline ({post_call_elapsed:.2f}s > {effective_deadline}s). Discarding response.")
                raise GeminiTimeoutError(f"Gemini API total deadline ({effective_deadline}s) exceeded.")

            if not response or not hasattr(response, "text"):
                raise GeminiClientError("Gemini returned an empty or invalid response structure.")
            return response.text

        except (exceptions.PermissionDenied, exceptions.Unauthenticated) as e:
            _log.error(f"Gemini authentication failed (non-transient): {str(e)}")
            raise GeminiAuthError(f"Gemini authentication failed: {str(e)}")

        except exceptions.InvalidArgument as e:
            _log.error(f"Gemini invalid argument / bad prompt (non-transient): {str(e)}")
            raise GeminiClientError(f"Gemini bad request: {str(e)}", status_code=400, is_transient=False)

        except exceptions.NotFound as e:
            _log.error(f"Gemini model or resource not found (non-transient): {str(e)}")
            raise GeminiClientError(f"Gemini resource not found: {str(e)}", status_code=404, is_transient=False)

        except exceptions.DeadlineExceeded as e:
            # Native provider transport socket deadline expired
            elapsed_now = time.monotonic() - start_time
            remaining_now = effective_deadline - elapsed_now
            _log.warning(f"Gemini transport socket deadline exceeded after {elapsed_now:.2f}s on attempt {attempt}.")
            
            if attempt > effective_max_retries or remaining_now <= 0.5:
                raise GeminiTimeoutError(f"Gemini API transport timeout after {elapsed_now:.2f}s across {attempt} attempts.")
            
            desired_backoff = 1.0 * attempt
            backoff = min(desired_backoff, remaining_now - 0.5)
            if backoff <= 0:
                raise GeminiTimeoutError(f"Gemini total deadline ({effective_deadline}s) expired during transport timeout backoff.")
            
            _log.warning(f"Retrying Gemini after transport timeout in {backoff:.1f}s (Attempt {attempt+1}/{effective_max_retries+1})...")
            time.sleep(backoff)

        except exceptions.ResourceExhausted as e:
            # 429 Rate limit
            elapsed_now = time.monotonic() - start_time
            remaining_now = effective_deadline - elapsed_now

            if attempt > effective_max_retries:
                _log.error(f"Gemini rate limit (429) hit and retries exhausted ({attempt} attempts).")
                raise GeminiRateLimitError("Gemini rate limit exceeded; max retries exhausted.")

            desired_backoff = 2.0 * attempt
            backoff = min(desired_backoff, remaining_now - 0.5)
            if backoff <= 0:
                raise GeminiTimeoutError("Gemini total deadline expired during rate limit backoff.")

            _log.warning(f"Gemini rate limit (429). Retrying in {backoff:.1f}s (Attempt {attempt+1}/{effective_max_retries+1})...")
            time.sleep(backoff)

        except (exceptions.ServiceUnavailable, exceptions.InternalServerError, exceptions.BadGateway, exceptions.GatewayTimeout) as e:
            # Transient 5xx server or gateway error (500, 502, 503, 504)
            elapsed_now = time.monotonic() - start_time
            remaining_now = effective_deadline - elapsed_now

            if attempt > effective_max_retries:
                _log.error(f"Gemini server error ({type(e).__name__}) and retries exhausted ({attempt} attempts): {str(e)}")
                raise GeminiServiceUnavailableError(f"Gemini service unavailable: {str(e)}")

            desired_backoff = 1.5 * attempt
            backoff = min(desired_backoff, remaining_now - 0.5)
            if backoff <= 0:
                raise GeminiTimeoutError("Gemini total deadline expired during server error backoff.")

            _log.warning(f"Gemini transient error ({type(e).__name__}). Retrying in {backoff:.1f}s (Attempt {attempt+1}/{effective_max_retries+1})... Error: {str(e)}")
            time.sleep(backoff)

        except GeminiClientError:
            # Explicitly re-raise custom exceptions (e.g. GeminiTimeoutError from late response check)
            raise

        except Exception as e:
            # Fallback string pattern inspection for untyped or wrapped exceptions
            elapsed_now = time.monotonic() - start_time
            remaining_now = effective_deadline - elapsed_now
            err_str = str(e).lower()

            if "unauthenticated" in err_str or "api_key_invalid" in err_str or "permission denied" in err_str or "401" in err_str or "403" in err_str:
                _log.error(f"Gemini authentication failed (non-transient): {str(e)}")
                raise GeminiAuthError(f"Gemini authentication failed: {str(e)}")

            if "invalid argument" in err_str or "400" in err_str:
                _log.error(f"Gemini invalid argument: {str(e)}")
                raise GeminiClientError(f"Gemini bad request: {str(e)}", status_code=400, is_transient=False)

            if "resource exhausted" in err_str or "rate limit" in err_str or "429" in err_str:
                if attempt > effective_max_retries:
                    raise GeminiRateLimitError("Gemini rate limit exceeded; max retries exhausted.")
                backoff = min(2.0 * attempt, remaining_now - 0.5)
                if backoff <= 0:
                    raise GeminiTimeoutError("Gemini total deadline expired during rate limit backoff.")
                time.sleep(backoff)
                continue

            if any(term in err_str for term in ["service unavailable", "503", "internal server", "500", "bad gateway", "502", "gateway timeout", "504"]):
                if attempt > effective_max_retries:
                    raise GeminiServiceUnavailableError(f"Gemini service unavailable: {str(e)}")
                backoff = min(1.5 * attempt, remaining_now - 0.5)
                if backoff <= 0:
                    raise GeminiTimeoutError("Gemini total deadline expired during server error backoff.")
                time.sleep(backoff)
                continue

            if "timeout" in err_str or "timed out" in err_str or "deadline exceeded" in err_str:
                if attempt <= effective_max_retries and remaining_now > 1.0:
                    backoff = min(1.0, remaining_now - 0.5)
                    _log.warning(f"Gemini connection timeout. Retrying in {backoff:.1f}s...")
                    time.sleep(backoff)
                    continue
                raise GeminiTimeoutError(f"Gemini connection timed out: {str(e)}")

            # Any other unknown error -> do not retry blindly
            _log.error(f"Gemini non-transient or unhandled error: {str(e)}", exc_info=True)
            raise GeminiClientError(f"Gemini call failed: {str(e)}", status_code=500, is_transient=False)
