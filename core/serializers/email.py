from rest_framework import serializers


class EmailSettingsSerializer(serializers.Serializer):
    smtp_host = serializers.CharField()
    smtp_port = serializers.IntegerField(min_value=1, max_value=65535)
    smtp_usuario = serializers.CharField()
    smtp_senha = serializers.CharField(write_only=True)
    smtp_ssl = serializers.BooleanField()
    email_from = serializers.EmailField()
