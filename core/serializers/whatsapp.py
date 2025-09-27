from rest_framework import serializers


class WhatsAppSettingsSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
    device_name = serializers.CharField()
    stealth_mode = serializers.BooleanField()
    human_delays = serializers.BooleanField()
    reconnect_backoff_seconds = serializers.IntegerField(min_value=0)

    # segredos (write_only) – respostas mascaradas na view
    session_data = serializers.CharField(allow_blank=True, required=False, write_only=True)
    proxy_url = serializers.CharField(allow_blank=True, required=False, write_only=True)


