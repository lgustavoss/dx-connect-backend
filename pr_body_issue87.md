# Fix: Consumer WebSocket processa inject_incoming e cria chats (Issue #87)

## Problema

O WebSocket conectava com sucesso, mas o consumer não processava completamente os eventos inject_incoming:
- Mensagem era salva no banco (WhatsAppMessage)
- Chat NÃO era criado (Atendimento + FilaAtendimento)
- Evento new_chat NÃO era emitido
- Frontend não recebia alerta de novo chat

## Solução

Integrado ChatService.processar_nova_mensagem_recebida() no consumer WebSocket.

## Mudanças

whatsapp/consumers.py (+7 linhas)
- Integra ChatService no receive_json
- Auto-cria Atendimento + Fila via WebSocket
- Emite evento new_chat com alerta sonoro
- Adiciona chat_id na resposta inject_success

## Fluxo Completo Agora

Frontend envia inject_incoming via WS → Consumer recebe → Cria WhatsAppMessage → ChatService.processar_nova_mensagem_recebida() → Cria Atendimento + Fila → Emite new_chat → Frontend recebe alerta

## Como Testar

1. Conectar WebSocket
2. Enviar inject_incoming
3. Verificar evento new_chat recebido
4. Verificar GET /api/v1/chats/ retorna chat criado

Closes #87

