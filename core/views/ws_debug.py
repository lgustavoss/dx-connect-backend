from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken


class WsDebugView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.query_params.get("token")
        if not token:
            return Response({"detail": "token é obrigatório"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            at = AccessToken(token)
            user_id = at.get("user_id")
            return Response({"pong": True, "user_id": user_id})
        except Exception:
            return Response({"detail": "token inválido"}, status=status.HTTP_403_FORBIDDEN)


