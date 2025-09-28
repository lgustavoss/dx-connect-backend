from __future__ import annotations

import asyncio
import contextlib
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
    return f"user_{user_id}:whatsapp"


@dataclass
class SessionState:
    status: str = "disconnected"
    task: Optional[asyncio.Task] = None


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
        await self.channel_layer.group_send(  # type: ignore[func-returns-value]
            user_group_name(user_id),
            {"type": "whatsapp.event", "event": payload},
        )

    async def start(self, user_id: int) -> Dict:
        state = self._sessions.get(user_id) or SessionState()
        if state.status in {"connecting", "qrcode", "authenticated", "ready"}:
            return {"status": state.status}

        state.status = "connecting"
        self._sessions[user_id] = state
        await self._emit(user_id, {"type": "session_status", "status": "connecting", "ts": now_iso()})

        async def run_connect_flow():
            try:
                await asyncio.sleep(self.connect_step)
                # QRCode fictício
                qr_data = base64.b64encode(b"stub-qr").decode()
                state.status = "qrcode"
                await self._emit(user_id, {"type": "session_status", "status": "qrcode", "ts": now_iso()})
                await self._emit(user_id, {"type": "qrcode", "image_b64": qr_data, "ts": now_iso()})

                await asyncio.sleep(self.connect_step)
                state.status = "authenticated"
                await self._emit(user_id, {"type": "session_status", "status": "authenticated", "ts": now_iso()})

                await asyncio.sleep(self.connect_step)
                state.status = "ready"
                await self._emit(user_id, {"type": "session_status", "status": "ready", "ts": now_iso()})
            except asyncio.CancelledError:
                # encerrado
                pass

        # criar tarefa de conexão
        loop = asyncio.get_running_loop()
        state.task = loop.create_task(run_connect_flow())
        return {"status": state.status}

    async def stop(self, user_id: int) -> None:
        state = self._sessions.get(user_id)
        if not state:
            return
        if state.task and not state.task.done():
            state.task.cancel()
            with contextlib.suppress(Exception):
                await state.task
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

        async def flow():
            statuses = [
                ("queued", 0.01),
                ("sent", 0.05),
                ("delivered", 0.05),
                ("read", 0.05),
            ]
            for s, delay in statuses:
                await asyncio.sleep(delay)
                await self._emit(
                    user_id,
                    {
                        "type": "message_status",
                        "message_id": message_id,
                        "status": s,
                        "ts": now_iso(),
                    },
                )

        loop = asyncio.get_running_loop()
        loop.create_task(flow())
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


