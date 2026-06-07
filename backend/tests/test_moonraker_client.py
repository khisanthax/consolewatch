from app.integrations.moonraker import MoonrakerClient


def test_moonraker_client_builds_websocket_url_and_payloads():
    client = MoonrakerClient("https://printer.local:7125", api_key="secret")

    assert client.websocket_url == "wss://printer.local:7125/websocket"
    assert client.headers == {"X-Api-Key": "secret"}
    assert client.identify_payload()["method"] == "server.connection.identify"
    assert client.subscription_payload()["method"] == "printer.objects.subscribe"
    assert "webhooks" in client.subscription_payload()["params"]["objects"]
