"""MCP server para a conversao de unidades de medida."""

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("unit-converter")

LENGTH_UNITS = {
    "mm": 0.001,
    "millimeter": 0.001,
    "millimeters": 0.001,
    "cm": 0.01,
    "centimeter": 0.01,
    "centimeters": 0.01,
    "m": 1.0,
    "meter": 1.0,
    "meters": 1.0,
    "km": 1000.0,
    "kilometer": 1000.0,
    "kilometers": 1000.0,
}

AREA_UNITS = {
    "m2": 1.0,
    "square meter": 1.0,
    "square meters": 1.0,
    "km2": 1_000_000.0,
    "square kilometer": 1_000_000.0,
    "square kilometers": 1_000_000.0,
    "ha": 10_000.0,
    "hectare": 10_000.0,
    "hectares": 10_000.0,
}


def _convert(value: float, from_unit: str, to_unit: str) -> float:
    f = from_unit.lower()
    t = to_unit.lower()
    if f in LENGTH_UNITS and t in LENGTH_UNITS:
        base = value * LENGTH_UNITS[f]
        return base / LENGTH_UNITS[t]
    if f in AREA_UNITS and t in AREA_UNITS:
        base = value * AREA_UNITS[f]
        return base / AREA_UNITS[t]
    raise ValueError("Unit not supported")


@mcp.tool()
async def convert(value: float, from_unit: str, to_unit: str) -> str:
    """Converte unidades de medida (comprimento ou área)."""
    result = _convert(value, from_unit, to_unit)
    return str(result)


if __name__ == "__main__":
    print("🚀 Iniciando MCP de conversão de unidade...")
    mcp.run()