from __future__ import annotations

from typing import Any, Dict

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from core.permissions import CanManageConfigWhatsApp
from integrations.whatsapp_stub import get_whatsapp_service


class WhatsAppSessionStartView(APIView):
    permission_classes = [IsAuthenticated, CanManageConfigWhatsApp]

    @extend_schema(operation_id="whatsapp_session_start", summary="Inicia sessão do WhatsApp (stub)")
    async def post(self, request):
        svc = get_whatsapp_service()
        data = await svc.start(request.user.id)
        return Response(data, status=status.HTTP_202_ACCEPTED)


class WhatsAppSessionStopView(APIView):
    permission_classes = [IsAuthenticated, CanManageConfigWhatsApp]

    @extend_schema(operation_id="whatsapp_session_stop", summary="Encerra sessão do WhatsApp (stub)")
    async def delete(self, request):
        svc = get_whatsapp_service()
        await svc.stop(request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class WhatsAppSessionStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(operation_id="whatsapp_session_status", summary="Consulta status da sessão (stub)")
    async def get(self, request):
        svc = get_whatsapp_service()
        data = await svc.get_status(request.user.id)
        return Response(data)


class WhatsAppSendMessageView(APIView):
    permission_classes = [IsAuthenticated, CanManageConfigWhatsApp]

    @extend_schema(operation_id="whatsapp_send_message", summary="Envia mensagem (stub)")
    async def post(self, request):
        payload: Dict[str, Any] = request.data or {}
        to = payload.get("to")
        msg_type = payload.get("type")
        if not to or not isinstance(to, str):
            return Response({"detail": "Campo 'to' é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        if msg_type not in {"text"}:
            return Response({"detail": "Campo 'type' inválido"}, status=status.HTTP_400_BAD_REQUEST)
        text = payload.get("text") if msg_type == "text" else None
        if msg_type == "text" and not text:
            return Response({"detail": "Campo 'text' é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)

        svc = get_whatsapp_service()
        try:
            data = await svc.send_message(request.user.id, to, {"type": "text", "text": text}, payload.get("client_message_id"))
        except RuntimeError:
            return Response({"detail": "Sessão não está pronta"}, status=status.HTTP_423_LOCKED)
        return Response(data, status=status.HTTP_202_ACCEPTED)


