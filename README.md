# MVP-Agent

O **MVP-Agent** é um agente de IA exposto via API, projetado para ser
personalizável e observável. A solução permite definir modelos, temperatura e
prompts em tempo de execução, além de integrar ferramentas externas do
ecossistema MCP.

- Documentação completa em [`docs/`](docs/README.md).
- Exemplos de utilização e boas práticas estão disponíveis no [Guia de Uso](docs/guia-de-uso.md).

## Pré-requisitos
- Python 3.12+
- Node.js 16+ (necessário para o MCP de Azure DevOps)
- [Poetry](https://python-poetry.org/) ou `pip` para gerenciamento de pacotes
- Docker (opcional para serviços externos)

## Instalação
```bash
pip install -r requirements.txt
```

## Execução
```bash
uvicorn src.api.main:app --reload
```
Acesse `http://localhost:8000/docs` para a interface interativa da API.
Um endpoint de _health check_ está disponível em `http://localhost:8000/health`.
Os logs de execução são salvos no diretório `logs/`.

### Executando o Broker e o Core Agent
Abra um terminal para o consumidor:

```bash
python -m src.core.core_agent
```

Em outro terminal, suba a API conforme acima.

### Console Interativo
Para conversar diretamente com o agente sem a API:

```bash
python main.py
```

### Teste de fluxo completo
Execute o script de exemplo que autentica, envia uma requisição e exibe a resposta:

```bash
python scripts/test_flow.py
```

### Utilizando o Core
O módulo `src.core` expõe uma fábrica `create_agent` para gerar instâncias configuráveis.
Exemplo de uso assíncrono:

```python
from src.core import create_agent

agent = await create_agent(model="gpt-4o", temperature=0.2)
response = await agent.run("Olá, tudo bem?")
```

Snapshots de memória são salvos em `checkpoints/` a cada interação.

## Testes
Execute `pytest` para rodar a suíte automatizada que cobre a criação do agente e integração via broker.

## Contribuindo
Contribuições são bem-vindas! Abra issues e pull requests sempre que possível.
Consulte a [Arquitetura](docs/arquitetura.md) para entender a organização do
projeto antes de propor mudanças significativas.