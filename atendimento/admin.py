from django.contrib import admin
from .models import Departamento, FilaAtendimento, Atendimento


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'max_atendimentos_simultaneos', 'tempo_resposta_esperado_minutos', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'descricao']
    filter_horizontal = ['atendentes']


@admin.register(FilaAtendimento)
class FilaAtendimentoAdmin(admin.ModelAdmin):
    list_display = ['id', 'departamento', 'cliente', 'prioridade', 'entrou_na_fila_em', 'atribuido_em']
    list_filter = ['departamento', 'prioridade', 'entrou_na_fila_em']
    search_fields = ['cliente__razao_social', 'numero_whatsapp']
    readonly_fields = ['entrou_na_fila_em', 'atribuido_em']


@admin.register(Atendimento)
class AtendimentoAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'cliente', 'atendente', 'departamento', 'status',
        'prioridade', 'criado_em', 'finalizado_em', 'avaliacao'
    ]
    list_filter = ['status', 'departamento', 'prioridade', 'criado_em']
    search_fields = ['cliente__razao_social', 'atendente__username', 'observacoes']
    readonly_fields = [
        'criado_em', 'iniciado_em', 'primeira_resposta_em', 'finalizado_em',
        'tempo_primeira_resposta_segundos', 'tempo_total_atendimento_segundos'
    ]

