import asyncio
import json
import os

from air import AsyncAIRefinery
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

# Default single-agent config
default_config = "config.yaml"
default_project = "evaluation_demo"

# Two-agent comparison config
compare_config = "config_two_agents.yaml"
compare_project = "evaluation_demo_compare"

# Register both projects at startup
client_init = AsyncAIRefinery(api_key=api_key, base_url=base_url)
client_init.distiller.create_project(config_path=default_config, project=default_project)
client_init.distiller.create_project(config_path=compare_config, project=compare_project)

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.websocket("/ws/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    print("WebSocket connection opened")

    ws_incoming: asyncio.Queue = asyncio.Queue()

    async def ws_reader():
        try:
            while True:
                raw = await websocket.receive_text()
                await ws_incoming.put(raw)
        except WebSocketDisconnect:
            await ws_incoming.put(None)

    reader_task = asyncio.create_task(ws_reader())
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)

    try:
        while True:
            raw = await ws_incoming.get()
            if raw is None:
                break
            user_query = json.loads(raw)["content"]
            print(f"QUERY: {user_query}\n")

            # Determine which config to use based on query
            if "compare" in user_query.lower():
                project_name = compare_project
                query = "OnlineSearcher and BusinessPlanner both work for me. Can you compare them to see which one is better?"
            else:
                project_name = default_project
                query = "Please evaluate the Search Agent."

            async with client.distiller(
                project=project_name,
                uuid=uuid,
            ) as dc:
                responses = await dc.query(query=query)

                async for response in responses:
                    if {"role", "content"}.issubset(response):
                        role = response.get("role", "")
                        content = response.get("content", "")

                        # Skip raw JSON dump section
                        cutoff_index = content.find("## Raw JSON output")
                        if cutoff_index != -1:
                            continue

                        agent_message = {"role": role, "content": content}
                        await websocket.send_text(
                            f"JSONSTART{json.dumps(agent_message)}JSONEND"
                        )
                        print(f"{role}: {content[:120]}\n")

            print("\n\n")
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {uuid}")
    finally:
        reader_task.cancel()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app_ui:app", host="0.0.0.0", port=8000)
