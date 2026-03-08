import json

from air import AsyncAIRefinery
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from auth import api_key, base_url, project_name

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.websocket("/ws/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    print("WebSocket connection opened")

    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)
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
