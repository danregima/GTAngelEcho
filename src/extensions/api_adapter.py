"""
External API Adapter — Exposes GTAngelEcho internals via REST/WebSocket.
Allows external tools, dashboards, and AI agents to observe and control
the cognitive architecture at runtime.

KSM Cycle 2: External connectivity for The Void (Property 13).
"""
import json
import time
import logging
import threading
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from http.server import HTTPServer, BaseHTTPRequestHandler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')
logger = logging.getLogger("APIAdapter")


@dataclass
class APIRoute:
    """A registered API route."""
    path: str
    method: str  # GET, POST, PUT, DELETE
    handler: Callable
    description: str = ""


class GTAngelEchoAPI:
    """
    External API Adapter for GTAngelEcho.

    Provides:
    - REST endpoints for querying system state
    - Command injection for external control
    - Plugin management via API
    - Event stream for real-time monitoring
    - Extensible route registration

    This adapter can run as a standalone HTTP server or be integrated
    into an existing web framework (FastAPI, Flask).
    """

    def __init__(self, angel_echo=None):
        self._angel = angel_echo
        self._routes: Dict[str, Dict[str, APIRoute]] = {}
        self._command_queue: List[Dict] = []
        self._event_stream: List[Dict] = []
        self._event_stream_max = 500
        self._server: Optional[HTTPServer] = None
        self._server_thread: Optional[threading.Thread] = None

        # Register built-in routes
        self._register_builtin_routes()
        logger.info("API Adapter initialized")

    def bind(self, angel_echo):
        """Bind to a GTAngelEcho instance (can be done after construction)."""
        self._angel = angel_echo

    # ── Route Registration ─────────────────────────────────────

    def route(self, path: str, method: str = "GET", description: str = ""):
        """Decorator to register an API route."""
        def decorator(handler: Callable):
            self.add_route(path, method, handler, description)
            return handler
        return decorator

    def add_route(self, path: str, method: str, handler: Callable, description: str = ""):
        """Register an API route programmatically."""
        method = method.upper()
        if path not in self._routes:
            self._routes[path] = {}
        self._routes[path][method] = APIRoute(
            path=path, method=method, handler=handler, description=description
        )

    def handle_request(self, method: str, path: str, body: Optional[Dict] = None) -> Dict:
        """
        Handle an API request.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: Request path (e.g., "/api/state")
            body: Optional request body for POST/PUT

        Returns:
            Response dict with "status", "data", and optional "error".
        """
        route_methods = self._routes.get(path)
        if not route_methods:
            return {"status": 404, "error": f"Route not found: {path}"}

        route = route_methods.get(method.upper())
        if not route:
            return {"status": 405, "error": f"Method {method} not allowed for {path}"}

        try:
            result = route.handler(body)
            return {"status": 200, "data": result}
        except Exception as e:
            logger.error(f"API error at {method} {path}: {e}")
            return {"status": 500, "error": str(e)}

    # ── Built-in Routes ────────────────────────────────────────

    def _register_builtin_routes(self):
        """Register all built-in API routes."""

        # System state
        self.add_route("/api/state", "GET", self._get_state,
                      "Get full system state (mode, hormones, metrics)")
        self.add_route("/api/metrics", "GET", self._get_metrics,
                      "Get performance metrics")
        self.add_route("/api/hormones", "GET", self._get_hormones,
                      "Get current hormone levels")
        self.add_route("/api/valence-arousal", "GET", self._get_valence_arousal,
                      "Get valence-arousal coordinates")

        # Control
        self.add_route("/api/command", "POST", self._post_command,
                      "Inject a command (event, config change)")
        self.add_route("/api/event", "POST", self._post_event,
                      "Signal a world event to the endocrine system")

        # Plugins
        self.add_route("/api/plugins", "GET", self._get_plugins,
                      "List all registered plugins")
        self.add_route("/api/plugins/enable", "POST", self._enable_plugin,
                      "Enable a plugin by name")
        self.add_route("/api/plugins/disable", "POST", self._disable_plugin,
                      "Disable a plugin by name")

        # Events
        self.add_route("/api/events", "GET", self._get_event_stream,
                      "Get recent event stream")
        self.add_route("/api/events/stats", "GET", self._get_event_stats,
                      "Get event emission statistics")

        # Hooks
        self.add_route("/api/hooks", "GET", self._get_hooks,
                      "List all hook points and handler counts")

        # Routes
        self.add_route("/api/routes", "GET", self._get_routes,
                      "List all registered API routes")

        # Memory
        self.add_route("/api/memory/recent", "GET", self._get_recent_memories,
                      "Get recent episodic memories")

    def _get_state(self, body=None) -> Dict:
        if not self._angel:
            return {"error": "No GTAngelEcho instance bound"}
        hormones = self._angel.endocrine.get_state()
        v, a = self._angel.endocrine.get_valence_arousal()
        return {
            "tick": self._angel.tick_count,
            "mode": self._angel.endocrine.current_mode.value,
            "valence": v,
            "arousal": a,
            "autonomy_level": self._angel.autonomy_level,
            "hormones": hormones,
            "metrics": self._angel.get_metrics(),
        }

    def _get_metrics(self, body=None) -> Dict:
        if not self._angel:
            return {"error": "No GTAngelEcho instance bound"}
        return self._angel.get_metrics()

    def _get_hormones(self, body=None) -> Dict:
        if not self._angel:
            return {"error": "No GTAngelEcho instance bound"}
        return self._angel.endocrine.get_state()

    def _get_valence_arousal(self, body=None) -> Dict:
        if not self._angel:
            return {"error": "No GTAngelEcho instance bound"}
        v, a = self._angel.endocrine.get_valence_arousal()
        return {"valence": v, "arousal": a, "mode": self._angel.endocrine.current_mode.value}

    def _post_command(self, body=None) -> Dict:
        if not body:
            return {"error": "No command body provided"}
        self._command_queue.append(body)
        return {"queued": True, "queue_size": len(self._command_queue)}

    def _post_event(self, body=None) -> Dict:
        if not self._angel or not body:
            return {"error": "No instance or body"}
        event_type = body.get("type", "CUSTOM_EVENT")
        intensity = body.get("intensity", 0.5)
        self._angel.endocrine.signal_event(event_type, intensity, source="api")
        return {"signaled": event_type, "intensity": intensity}

    def _get_plugins(self, body=None) -> List:
        if not self._angel or not hasattr(self._angel, 'plugin_registry'):
            return []
        return self._angel.plugin_registry.list_plugins()

    def _enable_plugin(self, body=None) -> Dict:
        if not body or "name" not in body:
            return {"error": "Plugin name required"}
        if not self._angel or not hasattr(self._angel, 'plugin_registry'):
            return {"error": "Plugin registry not available"}
        success = self._angel.plugin_registry.enable(body["name"], self._angel._get_plugin_context())
        return {"enabled": success, "name": body["name"]}

    def _disable_plugin(self, body=None) -> Dict:
        if not body or "name" not in body:
            return {"error": "Plugin name required"}
        if not self._angel or not hasattr(self._angel, 'plugin_registry'):
            return {"error": "Plugin registry not available"}
        success = self._angel.plugin_registry.disable(body["name"])
        return {"disabled": success, "name": body["name"]}

    def _get_event_stream(self, body=None) -> List:
        if not self._angel or not hasattr(self._angel, 'event_bus'):
            return []
        events = self._angel.event_bus.get_history(limit=50)
        return [{"type": e.type, "source": e.source, "data": e.data,
                 "timestamp": e.timestamp} for e in events]

    def _get_event_stats(self, body=None) -> Dict:
        if not self._angel or not hasattr(self._angel, 'event_bus'):
            return {}
        return self._angel.event_bus.get_stats()

    def _get_hooks(self, body=None) -> Dict:
        if not self._angel or not hasattr(self._angel, 'hook_system'):
            return {}
        return self._angel.hook_system.list_hooks()

    def _get_routes(self, body=None) -> List:
        routes = []
        for path, methods in self._routes.items():
            for method, route in methods.items():
                routes.append({
                    "path": route.path,
                    "method": route.method,
                    "description": route.description,
                })
        return routes

    def _get_recent_memories(self, body=None) -> List:
        if not self._angel:
            return []
        memories = self._angel.memory.recall_episodic(top_k=10)
        return memories

    # ── Command Processing ─────────────────────────────────────

    def process_commands(self) -> int:
        """Process queued commands. Call this each tick."""
        processed = 0
        while self._command_queue:
            cmd = self._command_queue.pop(0)
            cmd_type = cmd.get("type", "unknown")

            if cmd_type == "signal_event":
                self._angel.endocrine.signal_event(
                    cmd.get("event", "CUSTOM"),
                    cmd.get("intensity", 0.5),
                    source="api_command"
                )
            elif cmd_type == "set_autonomy":
                self._angel.autonomy_level = cmd.get("level", self._angel.autonomy_level)
            elif cmd_type == "reset_endocrine":
                self._angel.endocrine.reset()

            processed += 1

        return processed

    # ── Server ─────────────────────────────────────────────────

    def start_server(self, host: str = "0.0.0.0", port: int = 8765):
        """Start a simple HTTP server for the API (non-blocking)."""
        adapter = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                response = adapter.handle_request("GET", self.path)
                self.send_response(response.get("status", 200))
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            def do_POST(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(content_length)) if content_length else {}
                response = adapter.handle_request("POST", self.path, body)
                self.send_response(response.get("status", 200))
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())

            def log_message(self, format, *args):
                pass  # Suppress default logging

        self._server = HTTPServer((host, port), Handler)
        self._server_thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._server_thread.start()
        logger.info(f"API Server started on {host}:{port}")

    def stop_server(self):
        """Stop the HTTP server."""
        if self._server:
            self._server.shutdown()
            logger.info("API Server stopped")


if __name__ == "__main__":
    api = GTAngelEchoAPI()

    # Test route handling
    logger.info("=== API Adapter Demo ===")

    # List routes
    result = api.handle_request("GET", "/api/routes")
    logger.info(f"Routes: {len(result['data'])} registered")
    for r in result["data"]:
        logger.info(f"  {r['method']:6s} {r['path']:30s} {r['description']}")

    # Test 404
    result = api.handle_request("GET", "/api/nonexistent")
    logger.info(f"404 test: {result}")
