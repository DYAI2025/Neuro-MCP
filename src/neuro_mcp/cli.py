from __future__ import annotations

import argparse
import json
import sys

from pydantic import SecretStr

from .config import Settings
from .service import NeuroMCPService


def _settings_from_args(args: argparse.Namespace) -> Settings:
    if args.config:
        settings = Settings.from_file(args.config)
    else:
        if not args.brain_root or not args.code_root:
            raise SystemExit("brain_root and code_root are required when --config is not used")
        settings = Settings(
            brain_root=args.brain_root,
            code_root=args.code_root,
            data_dir=args.data_dir or ".neuro_mcp",
            bearer_token=args.bearer_token,
        )
    if args.data_dir:
        settings.data_dir = settings.data_dir.__class__(args.data_dir).expanduser().resolve()
    if args.bearer_token:
        settings.bearer_token = SecretStr(args.bearer_token)
    return settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="neuro-mcp")
    parser.add_argument("--config")
    parser.add_argument("--brain-root")
    parser.add_argument("--code-root")
    parser.add_argument("--data-dir")
    parser.add_argument("--bearer-token")

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("index")

    search_brain = subparsers.add_parser("search-brain")
    search_brain.add_argument("query")
    search_brain.add_argument("--top-k", type=int, default=5)

    search_code = subparsers.add_parser("search-code")
    search_code.add_argument("query")
    search_code.add_argument("--top-k", type=int, default=5)

    reconcile = subparsers.add_parser("reconcile")
    reconcile.add_argument("query")
    reconcile.add_argument("--top-k", type=int, default=5)

    gc = subparsers.add_parser("gc")
    gc.add_argument("--apply", action="store_true")

    subparsers.add_parser("digest")

    serve = subparsers.add_parser("serve")
    serve.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)

    get_note = subparsers.add_parser("get-note")
    get_note.add_argument("path")

    get_related = subparsers.add_parser("get-related")
    get_related.add_argument("path")
    get_related.add_argument("--top-k", type=int, default=5)

    ingest = subparsers.add_parser("ingest")
    ingest.add_argument("path")
    ingest.add_argument("--title", required=True)
    ingest.add_argument("--content", required=True)
    ingest.add_argument("--type", default="note")
    ingest.add_argument("--tags", nargs="*", default=[])
    ingest.add_argument("--decay-class", default="30d")

    subparsers.add_parser("status")

    subparsers.add_parser("check-interference")

    return parser


def _print(payload) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    settings = _settings_from_args(args)
    service = NeuroMCPService(settings)

    if args.command == "index":
        service.refresh()
        _print({"status": "indexed", "brain_root": str(settings.brain_root), "code_root": str(settings.code_root)})
        return 0

    if args.command == "search-brain":
        _print([result.model_dump(mode="json") for result in service.search_brain(args.query, top_k=args.top_k)])
        return 0

    if args.command == "search-code":
        _print([result.model_dump(mode="json") for result in service.search_codebase(args.query, top_k=args.top_k)])
        return 0

    if args.command == "reconcile":
        _print(service.reconcile(args.query, top_k=args.top_k).model_dump(mode="json"))
        return 0

    if args.command == "gc":
        _print(service.gc(dry_run=not args.apply).model_dump(mode="json"))
        return 0

    if args.command == "digest":
        _print(service.digest().model_dump(mode="json"))
        return 0

    if args.command == "serve":
        try:
            from .server import create_http_app, create_mcp_app
        except ModuleNotFoundError as exc:
            raise SystemExit(
                "The optional MCP dependency is not installed. Install with: pip install 'neuro-mcp-server[mcp]'"
            ) from exc

        if args.transport == "stdio":
            app = create_mcp_app(settings)
            app.run(transport="stdio")
            return 0

        import uvicorn

        settings.bind_host = args.host
        settings.bind_port = args.port
        app = create_http_app(settings)
        uvicorn.run(app, host=args.host, port=args.port)
        return 0

    if args.command == "get-note":
        _print(service.get_note(args.path))
        return 0

    if args.command == "get-related":
        _print(service.get_related(args.path, top_k=args.top_k))
        return 0

    if args.command == "ingest":
        _print(service.ingest_note(
            relative_path=args.path, title=args.title, content=args.content,
            note_type=args.type, tags=args.tags, decay_class=args.decay_class,
        ))
        return 0

    if args.command == "status":
        _print(service.status())
        return 0

    if args.command == "check-interference":
        _print(service.check_interference())
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
