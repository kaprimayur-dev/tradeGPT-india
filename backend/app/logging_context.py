import contextvars
import logging

_request_id_var = contextvars.ContextVar("request_id", default="")

def set_request_id(req_id: str):
    _request_id_var.set(req_id)

def get_request_id() -> str:
    return _request_id_var.get()

class RequestIdFilter(logging.Filter):
    """Filters logs to inject the current request ID from contextvars."""
    def filter(self, record):
        req_id = get_request_id()
        if req_id:
            # Display a short request ID prefix
            record.request_id = f" [req-{req_id[:8]}]"
        else:
            record.request_id = ""
        return True
