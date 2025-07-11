"""MCP server for unit conversions."""

from mcp.server.fastmcp import FastMCP
from pint import UnitRegistry

ureg = UnitRegistry()

mcp = FastMCP("unit-converter")

@mcp.tool()
async def convert(value: float, from_unit: str, to_unit: str) -> str:
    """Convert between measurement units."""
    quantity = value * ureg(from_unit)
    converted = quantity.to(to_unit)
    return str(converted.magnitude)


def main() -> None:
    mcp.run()
