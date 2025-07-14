# Especificação da API

## Sumário
- [Autenticação](#autenticacao)
- [Endpoints](#endpoints)
  - [/login](#login)
  - [/refresh](#refresh)
  - [/agent/query](#agentquery)
  - [/health](#health)
- [Exemplos de Requisição](#exemplos-de-requisicao)

## Autenticação
A API utiliza **JWT**. O token deve conter claims customizados, como `role` e
`permissions`, permitindo granularidade de acesso. Exemplo de payload de token:
```json
{
  "sub": "user123",
  "role": "admin",
  "permissions": ["query"],
  "exp": 1718923200
}
```

## Endpoints
### /login
`POST /login`
Realiza a autenticação e retorna um token JWT.

**Requisição**
```json
{
  "username": "alice",
  "password": "secreta"
}
```
**Resposta**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```

### /refresh
`POST /refresh`
Recebe um token expirado no cabeçalho **Authorization** e devolve um novo token
mantendo o mesmo `thread_id`.

**Resposta**
```json
{
  "access_token": "<jwt>",
  "token_type": "bearer"
}
```


### /agent/query
`POST /agent/query`
Processa uma consulta ao agente de IA.

**Schema do Request (Pydantic)**
```python
class QueryRequest(BaseModel):
    prompt: str
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    tools: list[str] = []
    timeout: int = Field(30, gt=0)
```
**Schema da Resposta**
```python
class QueryResponse(BaseModel):
    id: str
    response: str
    tools_used: list[str]
```

### /health
`GET /health`
Endpoint simples para checagem de vida da aplicação.

**Resposta**
```json
{ "status": "ok" }
```

## Exemplos de Requisição
### cURL
```bash
curl -X POST http://localhost:8000/agent/query \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Olá"}'
```

### httpie
```bash
http POST :8000/agent/query \
  Authorization:"Bearer <jwt>" \
  prompt="Olá" temperature:=0.7
```

Consulte a [Arquitetura](arquitetura.md) para entender o fluxo completo das
requisições.
