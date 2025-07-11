"""MCP server for currency conversions using exchangerate-api."""

import requests
from mcp.server.fastmcp import FastMCP

API_URL = "https://api.exchangerate-api.com/v4/latest/{}"

mcp = FastMCP("currency-converter")

@mcp.tool()
async def convert(amount: float, from_currency: str, to_currency: str) -> str:
    """Convert currencies using current commercial rates."""
    url = API_URL.format(from_currency.upper())
    resp = requests.get(url, timeout=10)
    data = resp.json()
    rates = data.get("rates", {})
    if to_currency.upper() not in rates:
        raise ValueError("Currency not found")
    rate = rates[to_currency.upper()]
    result = amount * rate
    return str(result)


def main() -> None:
    mcp.run()
