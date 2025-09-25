Gestão de Estado das Sessões de Chat (Presença do Atendente)

Problema: Controlar status (online/offline/ocupado) dos atendentes e indicadores de digitação.

Especificação técnica:
- Modelo: AgentPresence { agent_id, status: [online, offline, busy], updated_at }
- Indicadores de digitação: eventos typing_start/typing_stop via WS
- Controle de sessões ativas/inativas: heartbeat do cliente + timeout
- Permissões: supervisor vê por departamento; gerente global

Critérios de aceitação:
- [ ] Endpoints para consultar e alterar status
- [ ] Eventos WS para presença e typing
- [ ] Timeout para marcar offline automático


