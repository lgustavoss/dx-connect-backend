Sistema de Logs e Monitoramento

Problema: Observabilidade e troubleshooting quando a sessão WhatsApp cair.

Especificação técnica:
- Logs estruturados (JSON) com python-json-logger
- Correlation ID por request/processo (incluir em WS eventos)
- Métricas: latência de recebimento, taxa de reconexão, mensagens por minuto
- Healthcheck: endpoint de saúde da sessão WhatsApp e do WS
- Alertas: thresholds simples (log de WARN/ERROR + futura integração externa)

Critérios de aceitação:
- [ ] Configuração de logger JSON por ambiente
- [ ] Métricas básicas expostas (endpoint interno ou logs)
- [ ] Documentação de troubleshooting


