from django.contrib import admin
from .models import WhatsAppSession, WhatsAppMessage


@admin.register(WhatsAppSession)
class WhatsAppSessionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'usuario', 'status', 'phone_number', 'device_name',
        'connected_at', 'is_active', 'total_messages_sent',
        'total_messages_received', 'error_count'
    ]
    list_filter = ['status', 'is_active', 'created_at', 'updated_at']
    search_fields = ['usuario__username', 'phone_number', 'device_name']
    readonly_fields = [
        'created_at', 'updated_at', 'connected_at', 'disconnected_at',
        'last_message_at', 'total_messages_sent', 'total_messages_received',
        'uptime_seconds'
    ]
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('usuario', 'status', 'is_active')
        }),
        ('Dispositivo', {
            'fields': ('device_name', 'phone_number')
        }),
        ('Autenticação', {
            'fields': ('qr_code', 'session_data'),
            'classes': ('collapse',)
        }),
        ('Métricas', {
            'fields': (
                'total_messages_sent', 'total_messages_received',
                'last_message_at', 'uptime_seconds'
            )
        }),
        ('Erros', {
            'fields': ('last_error', 'error_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'connected_at', 'disconnected_at')
        }),
    )


@admin.register(WhatsAppMessage)
class WhatsAppMessageAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'message_id', 'session', 'usuario', 'direction',
        'message_type', 'contact_number', 'status', 'created_at',
        'total_latency_ms', 'is_latency_acceptable'
    ]
    list_filter = [
        'direction', 'message_type', 'status', 'is_from_me',
        'created_at'
    ]
    search_fields = [
        'message_id', 'client_message_id', 'contact_number',
        'contact_name', 'text_content', 'chat_id'
    ]
    readonly_fields = [
        'created_at', 'queued_at', 'sent_at', 'delivered_at', 'read_at',
        'latency_to_sent_ms', 'latency_to_delivered_ms', 'latency_to_read_ms',
        'total_latency_ms', 'is_latency_acceptable'
    ]
    fieldsets = (
        ('Identificação', {
            'fields': ('message_id', 'client_message_id', 'session', 'usuario')
        }),
        ('Direção e Tipo', {
            'fields': ('direction', 'message_type', 'is_from_me')
        }),
        ('Contato', {
            'fields': ('chat_id', 'contact_number', 'contact_name')
        }),
        ('Conteúdo', {
            'fields': ('text_content', 'media_url', 'media_mime_type', 'media_size')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Timestamps', {
            'fields': (
                'created_at', 'queued_at', 'sent_at', 'delivered_at', 'read_at'
            )
        }),
        ('Métricas de Latência', {
            'fields': (
                'latency_to_sent_ms', 'latency_to_delivered_ms',
                'latency_to_read_ms', 'total_latency_ms', 'is_latency_acceptable'
            ),
            'classes': ('collapse',)
        }),
        ('Payload Completo', {
            'fields': ('payload',),
            'classes': ('collapse',)
        }),
    )

