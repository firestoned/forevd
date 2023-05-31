"""
Test REST application.
"""

import fastapi


APP = fastapi.FastAPI()


@APP.get("/")
def root(request: fastapi.Request):
    """Simple WEB example that outputs the headers recieved."""
    return request.headers
