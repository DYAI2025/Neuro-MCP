from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from .config import Settings
from .service import NeuroMCPService


def create_mcp_app(settings: Settings):
    """
    Create a FastMCP app.

    This module intentionally imports the MCP SDK lazily so the core package can
    be tested without the optional dependency installed.
    """
    from mcp.server import FastMCP  # type: ignore

    service = NeuroMCPService(settings)
    mcp = FastMCP(settings.mcp_server_name, json_response=True)

    @mcp.tool()
    def search_brain(query: str, top_k: int = 5) -> dict[str, Any]:
        """Search the second brain. Returns freshness, precision, and file-existence flags."""
        results = service.search_brain(query, top_k=top_k)
        return {
            "query": query,
            "results": [result.model_dump(mode="json") for result in results],
        }

    @mcp.tool()
    def search_codebase(query: str, top_k: int = 5) -> dict[str, Any]:
        """Search the codebase. Code is the source of truth for current implementation state."""
        results = service.search_codebase(query, top_k=top_k)
        return {
            "query": query,
            "results": [result.model_dump(mode="json") for result in results],
        }

    @mcp.tool()
    def reconcile_brain_with_code(query: str, top_k: int = 5) -> dict[str, Any]:
        """Cross-check brain notes against the codebase and return contradictions."""
        report = service.reconcile(query, top_k=top_k)
        return report.model_dump(mode="json")

    @mcp.tool()
    def freshness_digest() -> dict[str, Any]:
        """Return current freshness and volatility digest for the knowledge base."""
        return service.digest().model_dump(mode="json")

    @mcp.tool()
    def run_garbage_collection(dry_run: bool = True) -> dict[str, Any]:
        """Evaluate stale notes and missing source links. Does not delete files by default."""
        return service.gc(dry_run=dry_run).model_dump(mode="json")

    @mcp.tool()
    def brain_get_note(path: str) -> dict[str, Any]:
        """Retrieve a specific brain note by its relative path within the vault.
        Returns full content, metadata, freshness state, and source file existence."""
        return service.get_note(path)

    @mcp.tool()
    def brain_get_related(path: str, top_k: int = 5) -> dict[str, Any]:
        """Find notes semantically related to a given note.
        Uses embedding similarity — finds conceptual connections, not just keyword matches."""
        return service.get_related(path, top_k=top_k)

    @mcp.tool()
    def brain_ingest_note(
        relative_path: str,
        title: str,
        content: str,
        note_type: str = "note",
        tags: list[str] | None = None,
        decay_class: str = "30d",
        source_precision: float = 0.7,
        claimed_dependencies: list[str] | None = None,
    ) -> dict[str, Any]:
        """Write a new note or update an existing one in the brain vault.
        Use this to persist discoveries, decisions, or analysis results back into the knowledge base."""
        return service.ingest_note(
            relative_path=relative_path, title=title, content=content,
            note_type=note_type, tags=tags or [], decay_class=decay_class,
            source_precision=source_precision, claimed_dependencies=claimed_dependencies or [],
        )

    @mcp.tool()
    def brain_status() -> dict[str, Any]:
        """Return overall brain health: note counts by type, status, freshness, mode, and recommendations."""
        return service.status()

    @mcp.tool()
    def check_interference() -> dict[str, Any]:
        """Detect overlapping or near-duplicate brain notes using embedding similarity.
        Returns merge/cross-link candidates above the similarity threshold."""
        return service.check_interference()

    @mcp.resource("brain://digest/stale")
    def stale_digest_resource() -> str:
        digest = service.digest()
        return digest.model_dump_json(indent=2)

    @mcp.prompt()
    def grounded_answer_prompt(question: str) -> str:
        return (
            "Answer the question using search_brain and search_codebase. "
            "If they disagree, code wins. Mention freshness and precision. "
            f"Question: {question}"
        )

    return mcp


def create_http_app(settings: Settings):
    from starlette.applications import Starlette
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, PlainTextResponse, Response
    from starlette.routing import Mount, Route

    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager  # type: ignore

    mcp_app = create_mcp_app(settings)
    session_manager = StreamableHTTPSessionManager(app=mcp_app)

    class OriginGuardMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if request.url.path.startswith(settings.mcp_path):
                origin = request.headers.get("origin")
                if origin and origin not in settings.allowed_origins:
                    return PlainTextResponse("Origin not allowed", status_code=403)
            return await call_next(request)

    class BearerAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            if not request.url.path.startswith(settings.mcp_path):
                return await call_next(request)
            if not settings.bearer_token:
                return await call_next(request)
            if request.method == "OPTIONS":
                return await call_next(request)
            token = request.headers.get("authorization", "")
            expected = f"Bearer {settings.bearer_token}"
            if token == expected:
                return await call_next(request)
            metadata_url = settings.external_auth_metadata_url or "/.well-known/oauth-protected-resource"
            headers = {
                "WWW-Authenticate": f'Bearer realm="mcp", resource_metadata="{metadata_url}"'
            }
            return Response(status_code=401, headers=headers)

    async def health(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ok"})

    async def readiness(_: Request) -> JSONResponse:
        return JSONResponse({"status": "ready"})

    async def protected_resource_metadata(request: Request) -> JSONResponse:
        base = str(request.base_url).rstrip("/")
        resource = f"{base}{settings.mcp_path}"
        payload = {
            "resource": resource,
            "authorization_servers": [settings.external_auth_metadata_url] if settings.external_auth_metadata_url else [],
            "scopes_supported": ["mcp.read"],
            "bearer_methods_supported": ["header"],
        }
        return JSONResponse(payload)

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    app = Starlette(
        routes=[
            Route("/healthz", health),
            Route("/readyz", readiness),
            Route("/.well-known/oauth-protected-resource", protected_resource_metadata),
            Mount(settings.mcp_path, app=session_manager.handle_request),
        ],
        lifespan=lifespan,
    )
    app.add_middleware(OriginGuardMiddleware)
    if settings.bearer_token:
        app.add_middleware(BearerAuthMiddleware)
    return app
