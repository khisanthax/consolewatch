import json
from collections.abc import AsyncIterator
from urllib.parse import urlparse, urlunparse


class MoonrakerClient:
    def __init__(self, base_url: str, api_key: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    @property
    def websocket_url(self) -> str:
        parsed = urlparse(self.base_url)
        scheme = "wss" if parsed.scheme == "https" else "ws"
        return urlunparse((scheme, parsed.netloc, "/websocket", "", "", ""))

    @property
    def headers(self) -> dict[str, str]:
        if not self.api_key:
            return {}
        return {"X-Api-Key": self.api_key}

    @staticmethod
    def identify_payload(client_name: str = "ConsoleWatch") -> dict:
        return {
            "jsonrpc": "2.0",
            "method": "server.connection.identify",
            "params": {
                "client_name": client_name,
                "version": "0.1.0",
                "type": "other",
                "url": "https://github.com/khisanthax/consolewatch",
            },
            "id": 1,
        }

    @staticmethod
    def subscription_payload() -> dict:
        return {
            "jsonrpc": "2.0",
            "method": "printer.objects.subscribe",
            "params": {
                "objects": {
                    "webhooks": ["state", "state_message"],
                    "print_stats": ["state", "filename", "message"],
                }
            },
            "id": 2,
        }

    async def listen_notifications(self) -> AsyncIterator[dict]:
        import websockets

        async with websockets.connect(self.websocket_url, additional_headers=self.headers) as websocket:
            await websocket.send(json.dumps(self.identify_payload()))
            await websocket.send(json.dumps(self.subscription_payload()))
            async for message in websocket:
                payload = json.loads(message)
                if "method" in payload and "id" not in payload:
                    yield payload
