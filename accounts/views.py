from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import AgentGroupsSerializer, GroupSerializer, PermissionSerializer
from core.permissions import CanManageAuth


User = get_user_model()


class PermissionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, _request):
        qs = Permission.objects.select_related("content_type").order_by(
            "content_type__app_label", "content_type__model", "codename"
        )
        data = PermissionSerializer(qs, many=True).data
        return Response(data)


class GroupListCreateView(APIView):
    permission_classes = [IsAuthenticated, CanManageAuth]

    def get(self, _request):
        groups = Group.objects.all().order_by("name")
        return Response(GroupSerializer(groups, many=True).data)

    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        group = Group.objects.create(name=serializer.validated_data["name"])
        if serializer.validated_data.get("permissions"):
            group.permissions.set(serializer.validated_data["permissions"])
        return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)


class GroupDetailView(APIView):
    permission_classes = [IsAuthenticated, CanManageAuth]

    def get_object(self, pk: int) -> Group:
        return Group.objects.get(pk=pk)

    def get(self, _request, pk: int):
        group = self.get_object(pk)
        return Response(GroupSerializer(group).data)

    def patch(self, request, pk: int):
        group = self.get_object(pk)
        serializer = GroupSerializer(instance=group, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if "name" in serializer.validated_data:
            group.name = serializer.validated_data["name"]
        if "permissions" in serializer.validated_data:
            group.permissions.set(serializer.validated_data["permissions"])  # overwrite
        group.save()
        return Response(GroupSerializer(group).data)

    def delete(self, _request, pk: int):
        group = self.get_object(pk)
        group.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AgentGroupsView(APIView):
    permission_classes = [IsAuthenticated, CanManageAuth]

    def get(self, _request, agent_id: int):
        user = User.objects.get(pk=agent_id)
        groups = user.groups.all().order_by("name")
        return Response(GroupSerializer(groups, many=True).data)

    def patch(self, request, agent_id: int):
        user = User.objects.get(pk=agent_id)
        serializer = AgentGroupsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data["group_ids"]
        groups = Group.objects.filter(id__in=ids)
        user.groups.set(groups)
        return Response(GroupSerializer(user.groups.all(), many=True).data)


