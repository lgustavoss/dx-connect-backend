import contextvars
from uuid import uuid4
from typing import Callable
from django.http import HttpRequest, HttpResponse

# Contexto usado pelo filtro de logging
request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")


class RequestIdMiddleware:
    """Gera e propaga um X-Request-Id por requisição.

    - Lê de X-Request-Id (se enviado pelo cliente) ou gera novo UUID (hex)
    - Atribui em request.id e no ContextVar para logging
    - Escreve o header X-Request-Id na resposta
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        incoming_id = request.META.get("HTTP_X_REQUEST_ID")
        request_id = incoming_id or uuid4().hex
        # Disponibiliza na request e no contexto
        setattr(request, "id", request_id)
        request_id_var.set(request_id)

        response = self.get_response(request)
        response["X-Request-Id"] = request_id
        return response
