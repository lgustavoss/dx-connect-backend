from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core.models import Config
from core.serializers import ConfigSerializer


class ConfigView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self) -> Config:
        obj, _ = Config.objects.get_or_create()
        return obj

    def get(self, _request):
        obj = self.get_object()
        data = ConfigSerializer(obj).data
        return Response(data)

    def put(self, request):
        obj = self.get_object()
        serializer = ConfigSerializer(instance=obj, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
