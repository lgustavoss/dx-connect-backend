from rest_framework import serializers


class AppearanceSettingsSerializer(serializers.Serializer):
    login_logo_url = serializers.CharField(allow_blank=True, required=False)
    favicon_url = serializers.CharField(allow_blank=True, required=False)
    primary_color = serializers.CharField(allow_blank=True, required=False)
    secondary_color = serializers.CharField(allow_blank=True, required=False)
    custom_css = serializers.CharField(allow_blank=True, required=False)


