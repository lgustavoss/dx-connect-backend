from __future__ import annotations

import asyncio
import contextlib
import threading
import base64
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def user_group_name(user_id: int) -> str:
    return f"user_{user_id}_whatsapp"


@dataclass
class SessionState:
    status: str = "disconnected"
    task: Optional[asyncio.Task] = None
    timers: list[threading.Timer] = None  # type: ignore[assignment]


class StubWhatsAppSessionService:
    """Serviço stub para simular sessão e mensagens do WhatsApp.

    - Estados: disconnected -> connecting -> qrcode -> authenticated -> ready
    - Eventos enviados para o grupo de usuário: user_{id}:whatsapp
    - Mensagens: emite message_status (queued -> sent -> delivered -> read)
    """

    _sessions: Dict[int, SessionState] = {}

    def __init__(self, connect_step_ms: int = 100):
        self.connect_step = max(0, connect_step_ms) / 1000.0
        self.channel_layer = get_channel_layer()

    async def _emit(self, user_id: int, payload: Dict):
        layer = get_channel_layer()
        if not layer:
            return
        await layer.group_send(  # type: ignore[func-returns-value]
            user_group_name(user_id),
            {"type": "whatsapp.event", "event": payload},
        )

    def _emit_sync(self, user_id: int, payload: Dict):
        layer = get_channel_layer()
        if not layer:
            return
        async_to_sync(layer.group_send)(
            user_group_name(user_id),
            {"type": "whatsapp.event", "event": payload},
        )

    async def start(self, user_id: int) -> Dict:
        state = self._sessions.get(user_id) or SessionState()
        if state.status in {"connecting", "qrcode", "authenticated", "ready"}:
            return {"status": state.status}

        state.status = "connecting"
        state.timers = []
        self._sessions[user_id] = state
        await self._emit(user_id, {"type": "session_status", "status": "connecting", "ts": now_iso()})

        def step_qr():
            qr_data = base64.b64encode(b"stub-qr").decode()
            state.status = "qrcode"
            self._emit_sync(user_id, {"type": "session_status", "status": "qrcode", "ts": now_iso()})
            self._emit_sync(user_id, {"type": "qrcode", "image_b64": qr_data, "ts": now_iso()})

        def step_authenticated():
            state.status = "authenticated"
            self._emit_sync(user_id, {"type": "session_status", "status": "authenticated", "ts": now_iso()})

        def step_ready():
            state.status = "ready"
            self._emit_sync(user_id, {"type": "session_status", "status": "ready", "ts": now_iso()})

        # agendar transições por timers (compatível com contexto síncrono)
        t1 = threading.Timer(self.connect_step, step_qr)
        t2 = threading.Timer(self.connect_step * 2, step_authenticated)
        t3 = threading.Timer(self.connect_step * 3, step_ready)
        for t in (t1, t2, t3):
            t.daemon = True
            t.start()
        state.timers.extend([t1, t2, t3])
        return {"status": state.status}

    async def stop(self, user_id: int) -> None:
        state = self._sessions.get(user_id)
        if not state:
            return
        # cancelar timers
        for t in list(state.timers or []):
            try:
                t.cancel()
            except Exception:
                pass
        state.timers = []
        state.status = "disconnected"
        await self._emit(user_id, {"type": "session_status", "status": "disconnected", "ts": now_iso()})

    async def get_status(self, user_id: int) -> Dict:
        state = self._sessions.get(user_id) or SessionState()
        self._sessions[user_id] = state
        return {"status": state.status}

    async def send_message(self, user_id: int, to: str, payload: Dict, client_message_id: Optional[str] = None) -> Dict:
        state = self._sessions.get(user_id) or SessionState()
        if state.status != "ready":
            raise RuntimeError("session_not_ready")
        message_id = client_message_id or str(uuid.uuid4())

        def schedule_status(s: str, delay: float):
            def emit():
                self._emit_sync(
                    user_id,
                    {
                        "type": "message_status",
                        "message_id": message_id,
                        "status": s,
                        "ts": now_iso(),
                    },
                )
            t = threading.Timer(delay, emit)
            t.daemon = True
            t.start()
            (self._sessions[user_id].timers or []).append(t)

        schedule_status("queued", 0.0)
        schedule_status("sent", 0.05)
        schedule_status("delivered", 0.10)
        schedule_status("read", 0.15)
        return {"message_id": message_id}

    async def inject_incoming(self, user_id: int, from_number: str, payload: Dict) -> Dict:
        state = self._sessions.get(user_id) or SessionState()
        if state.status != "ready":
            raise RuntimeError("session_not_ready")
        message_id = str(uuid.uuid4())
        await self._emit(
            user_id,
            {
                "type": "message_received",
                "message_id": message_id,
                "from": from_number,
                "chat_id": from_number,
                "payload": payload,
                "ts": now_iso(),
            },
        )
        return {"message_id": message_id}


# Fábrica simples baseada em env/setting (por ora só stub)
_service = StubWhatsAppSessionService()


def get_whatsapp_service() -> StubWhatsAppSessionService:
    return _service


