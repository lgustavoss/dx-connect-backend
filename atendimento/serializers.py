from rest_framework import serializers
from .models import Departamento, FilaAtendimento, Atendimento


class DepartamentoSerializer(serializers.ModelSerializer):
    total_atendentes = serializers.IntegerField(source='atendentes.count', read_only=True)
    total_em_fila = serializers.SerializerMethodField()
    total_em_atendimento = serializers.SerializerMethodField()
    
    class Meta:
        model = Departamento
        fields = [
            'id', 'nome', 'descricao', 'cor', 'atendentes',
            'max_atendimentos_simultaneos', 'tempo_resposta_esperado_minutos',
            'ativo', 'total_atendentes', 'total_em_fila',
            'total_em_atendimento', 'criado_em', 'atualizado_em'
        ]
    
    def get_total_em_fila(self, obj):
        return obj.fila.filter(atribuido_em__isnull=True).count()
    
    def get_total_em_atendimento(self, obj):
        return obj.atendimentos.filter(status='em_atendimento').count()


class FilaAtendimentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.razao_social', read_only=True)
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    tempo_espera_minutos = serializers.IntegerField(read_only=True)
    esta_atrasado = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = FilaAtendimento
        fields = [
            'id', 'departamento', 'departamento_nome', 'cliente',
            'cliente_nome', 'chat_id', 'numero_whatsapp',
            'mensagem_inicial', 'prioridade', 'entrou_na_fila_em',
            'atribuido_em', 'tempo_espera_minutos', 'esta_atrasado'
        ]
        read_only_fields = ['id', 'entrou_na_fila_em', 'atribuido_em']


class AtendimentoSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.razao_social', read_only=True)
    atendente_nome = serializers.CharField(source='atendente.username', read_only=True)
    departamento_nome = serializers.CharField(source='departamento.nome', read_only=True)
    tempo_espera_minutos = serializers.IntegerField(read_only=True)
    duracao_minutos = serializers.IntegerField(read_only=True)
    esta_ativo = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Atendimento
        fields = [
            'id', 'departamento', 'departamento_nome', 'cliente',
            'cliente_nome', 'atendente', 'atendente_nome', 'chat_id',
            'numero_whatsapp', 'status', 'prioridade',
            'tempo_primeira_resposta_segundos', 'tempo_total_atendimento_segundos',
            'total_mensagens_cliente', 'total_mensagens_atendente',
            'avaliacao', 'comentario_avaliacao', 'observacoes',
            'criado_em', 'iniciado_em', 'primeira_resposta_em',
            'finalizado_em', 'tempo_espera_minutos', 'duracao_minutos',
            'esta_ativo'
        ]
        read_only_fields = [
            'id', 'criado_em', 'iniciado_em', 'primeira_resposta_em',
            'finalizado_em', 'tempo_primeira_resposta_segundos',
            'tempo_total_atendimento_segundos'
        ]


class AtendimentoListSerializer(serializers.ModelSerializer):
    cliente_nome = serializers.CharField(source='cliente.razao_social', read_only=True)
    atendente_nome = serializers.CharField(source='atendente.username', read_only=True)
    duracao_minutos = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Atendimento
        fields = [
            'id', 'cliente_nome', 'atendente_nome', 'status',
            'prioridade', 'duracao_minutos', 'criado_em'
        ]

