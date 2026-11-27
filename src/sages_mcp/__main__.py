"""Command-line entry point: `sages-mcp` or `python -m sages_mcp`."""

from __future__ import annotations

import argparse
import logging
import sys

import structlog

from sages_mcp import __version__
from sages_mcp.server import build_server

DEFAULT_PORT = 8000


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="sages-mcp",
        description="MCP server for Sages: seven teacher portrayals with source-verified passages.",
    )
    parser.add_argument(
        "--transport",
        choices=("stdio", "streamable-http"),
        default="stdio",
        help="stdio for a local client (default), streamable-http to listen on a port",
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="port for streamable-http")
    parser.add_argument("--version", action="version", version=f"sages-mcp {__version__}")
    return parser.parse_args(argv)


def configure_logging() -> None:
    """Structured logs on stderr. stdout belongs to the MCP protocol on the stdio transport."""
    logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(message)s")
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging()
    log = structlog.get_logger("sages_mcp")
    try:
        server = build_server()
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        return 1
    options = {"port": args.port} if args.transport == "streamable-http" else {}
    log.info("starting", transport=args.transport, version=__version__, **options)
    server.run(args.transport, **options)
    return 0


if __name__ == "__main__":
    sys.exit(main())
