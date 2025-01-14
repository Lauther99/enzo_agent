from src.app import app
from starlette.middleware.base import BaseHTTPMiddleware

# Middleware para manejar cabeceras de proxies
app.add_middleware(BaseHTTPMiddleware, dispatch=lambda request, call_next: call_next(request))

# uvicorn src.app:app --host 0.0.0.0 --port 5000 --reload
