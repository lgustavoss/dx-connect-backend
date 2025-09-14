from rest_framework import serializers


class BusinessHoursSerializer(serializers.Serializer):
    inicio = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    fim = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class ChatSettingsSerializer(serializers.Serializer):
    mensagem_saudacao = serializers.CharField()
    mensagem_fora_expediente = serializers.CharField()
    mensagem_encerramento = serializers.CharField()
    mensagem_inatividade = serializers.CharField()
    timeout_inatividade_minutos = serializers.IntegerField(min_value=1)
    limite_chats_simultaneos = serializers.IntegerField(min_value=1)
    horario_funcionamento = serializers.DictField(
        child=BusinessHoursSerializer(),
    )
