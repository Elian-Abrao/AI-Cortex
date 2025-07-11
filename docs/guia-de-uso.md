- Docker (opcional para serviços externos)
- Make (opcional)

## Configuração do Ambiente
1. Clone o repositório e instale as dependências:
   ```bash
   git clone <repo-url>
   cd MVP-Agent
   pip install -r requirements.txt
   ```
2. Defina as variáveis de ambiente em `.env` ou exporte diretamente:
   ```bash
   export BROKER_URL=redis://localhost:6379/0
   export OPENAI_API_KEY=<sua-chave>
   export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
   ```
3. (Opcional) Suba um Redis para filas assíncronas e um Prometheus para
   coleta de métricas.

## Execução Local
1. Inicie o serviço FastAPI:
   ```bash
   uvicorn src.api.main:app --reload
   ```
2. A API ficará disponível em `http://localhost:8000`.
3. Em um segundo terminal, inicie o consumidor do broker:
   ```bash
   python -m src.core.core_agent
   ```
4. Verifique a saúde da API acessando:
   ```bash
   curl http://localhost:8000/health
   ```
5. Para enviar uma requisição:
   ```bash
   curl -X POST http://localhost:8000/agent/query \
        -H "Authorization: Bearer <jwt>" \
        -H "Content-Type: application/json" \
        -d '{"prompt": "Olá"}'
   ```

## Exemplo de Token JWT
Abaixo um exemplo de token (header e payload) com claim customizada `role`:
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
.
{
  "sub": "user123",
  "role": "admin",
  "permissions": ["query"],
  "exp": 1718923200
}
```

## Observabilidade
- **Logs**: utilize o módulo `logging` com emojis para facilitar a leitura. Os arquivos de log ficam em `logs/`:
  ```python
  logger.info("🚀 Iniciando requisição %s", request_id)
  logger.error("❌ Erro: %s", erro)
  ```
- **Tracing**: configure o OpenTelemetry em `src/api/main.py` para exportar
  spans ao coletor:
  ```python
  from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
  FastAPIInstrumentor.instrument_app(app)
  ```
- **Métricas**: exponha métricas via Prometheus usando `prometheus-client` e
  configure seu Prometheus para coletar em `/metrics`.

Para mais detalhes de arquitetura, consulte [Arquitetura](arquitetura.md).