"""MCP server para a conversao de moedas."""

import requests
from mcp.server.fastmcp import FastMCP

API_URL = "https://api.exchangerate-api.com/v4/latest/{}"

mcp = FastMCP("currency-converter")

@mcp.tool()
async def converter_moedas(amount: float, from_currency: str, to_currency: str) -> str:
    """Realiza a conversao de uma quantia de uma moeda para outra.

    Args:
        amount (float): Quantia a ser convertida.
        from_currency (str): Moeda de origem (ex: "USD").
        to_currency (str): Moeda de destino (ex: "EUR").

    Retorna:
        str: Quantia convertida como string.
    Raises:
        ValueError: "Currency not found" - Se a moeda nao for encontrada.
    """
    url = API_URL.format(from_currency.upper())
    resp = requests.get(url, timeout=10)
    data = resp.json()
    rates = data.get("rates", {})
    if to_currency.upper() not in rates:
        raise ValueError("Currency not found")
    rate = rates[to_currency.upper()]
    result = amount * rate
    return str(result)

@mcp.tool()
async def obter_cotacao(base: str = "BRL", moedas: list[str] | None = None) -> dict:
    """
    Retorna a cotação atual de uma ou mais moedas em relação à moeda base.

    Args:
        base (str): Moeda base (ex: "BRL", "USD").
        moedas (list[str], opcional): Lista de moedas-alvo para filtrar (ex: ["EUR", "USD"]). Se None, retorna todas.

    Returns:
        dict: Dicionário com as cotações das moedas solicitadas.
    """
    url = API_URL.format(base.upper())
    resp = requests.get(url, timeout=10)
    data = resp.json()
    rates = data.get("rates", {})

    if moedas:
        moedas_upper = [m.upper() for m in moedas]
        filtered = {moeda: rates.get(moeda, "❌ Não encontrada") for moeda in moedas_upper}
        return filtered

    return rates


if __name__ == "__main__":
    mcp.run()