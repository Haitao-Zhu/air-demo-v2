import asyncio
import json
import os

from air import AsyncAIRefinery
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

AZURE_CONFIG = "config_azure.yaml"
FALLBACK_CONFIG = "config.yaml"
AZURE_PROJECT = "marketing_agents_v2_azure"
FALLBACK_PROJECT = "marketing_agents_v2"

client = AsyncAIRefinery(api_key=api_key, base_url=base_url)


def _init_project():
    """Try Azure with real connection test, auto-fallback for UI."""
    # Register Azure config
    try:
        client.distiller.create_project(config_path=AZURE_CONFIG, project=AZURE_PROJECT)
    except Exception as e:
        print(f">>> Azure config registration failed: {e}")
        client.distiller.create_project(config_path=FALLBACK_CONFIG, project=FALLBACK_PROJECT)
        print(f">>> Using fallback agents (project: {FALLBACK_PROJECT})")
        return FALLBACK_PROJECT

    # Test Azure connection
    try:
        from azure.ai.projects import AIProjectClient  # noqa: F401

        async def _test():
            async with client.distiller(
                project=AZURE_PROJECT, uuid="azure_test"
            ) as dc:
                pass

        asyncio.run(_test())
        print(f">>> Using Azure AI agents (project: {AZURE_PROJECT})")
        return AZURE_PROJECT
    except Exception as e:
        print(f">>> Azure connection test failed: {e}")
        client.distiller.create_project(config_path=FALLBACK_CONFIG, project=FALLBACK_PROJECT)
        print(f">>> Using fallback agents (project: {FALLBACK_PROJECT})")
        return FALLBACK_PROJECT


project_name = _init_project()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.websocket("/ws/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    print("WebSocket connection opened")

    try:
        while True:
            json_obj = await websocket.receive_text()
            user_query = json.loads(json_obj)["content"]
            print(f"QUERY: {user_query}\n")
            async with client.distiller(
                project=project_name,
                uuid=uuid,
            ) as dc:
                responses = await dc.query(query=user_query)
                async for response in responses:
                    if {"role", "content"}.issubset(response):
                        agent_message = {
                            "role": response["role"],
                            "content": response["content"],
                        }
                        await websocket.send_text(
                            f"JSONSTART{json.dumps(agent_message)}JSONEND"
                        )
                        print(f"{response['role']}: {response['content'][:120]}\n")
            print("\n\n")
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {uuid}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app_ui:app", host="0.0.0.0", port=8000)
