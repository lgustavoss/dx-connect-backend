from typing import Any
from core.middleware import request_id_var


class RequestIdLogFilter:
    """Filtro para incluir request_id nos registros de log.

    Evita dependências de Django apps/models para não quebrar a inicialização
    do LOGGING durante o boot do Django.
    """

    def filter(self, record: Any) -> bool:
        try:
            record.request_id = request_id_var.get()
        except Exception:
            record.request_id = "-"
        return True
