import asyncio
import json

from air import AsyncAIRefinery
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from auth import api_key, base_url, project_name

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Per-session queue: user's WebSocket messages go here so the HumanAgent
# executor can read them while the response stream is being processed.
human_input_queues: dict[str, asyncio.Queue] = {}


def make_human_input_func(session_id: str):
    """Return an async callable that the HumanAgent executor will use
    instead of terminal input.  It blocks until the user sends a
    WebSocket message (routed here by the reader task)."""

    async def human_input_from_ws(query: str) -> str:
        q = human_input_queues.get(session_id)
        if q is None:
            return "confirmed"
        return await q.get()

    return human_input_from_ws


@app.get("/")
async def read_index():
    return FileResponse("static/index.html")


@app.websocket("/ws/{uuid}")
async def websocket_endpoint(websocket: WebSocket, uuid: str):
    await websocket.accept()
    print("WebSocket connection opened")

    human_input_queues[uuid] = asyncio.Queue()
    # Queue for incoming user messages (first message starts the query,
    # subsequent messages during a query are routed to HumanAgent)
    ws_incoming: asyncio.Queue = asyncio.Queue()

    async def ws_reader():
        """Read all WebSocket messages into ws_incoming."""
        try:
            while True:
                raw = await websocket.receive_text()
                await ws_incoming.put(raw)
        except WebSocketDisconnect:
            await ws_incoming.put(None)  # Sentinel

    reader_task = asyncio.create_task(ws_reader())
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)

    try:
        while True:
            # Wait for the user to send a query
            raw = await ws_incoming.get()
            if raw is None:
                break
            user_query = json.loads(raw)["content"]
            print(f"QUERY: {user_query}\n")

            # Drain stale human input
            while not human_input_queues[uuid].empty():
                human_input_queues[uuid].get_nowait()

            async with client.distiller(
                project=project_name,
                uuid=uuid,
                executor_dict={
                    "Tech Confirmation": make_human_input_func(uuid),
                },
            ) as dc:
                responses = await dc.query(query=user_query)

                # Process response stream. While iterating, the SDK may call
                # the HumanAgent executor which blocks on human_input_queues.
                # A separate task feeds that queue from ws_incoming.
                human_relay_active = False

                async def human_relay():
                    """Forward WebSocket messages to the HumanAgent queue
                    while the executor is waiting for human input."""
                    nonlocal human_relay_active
                    while human_relay_active:
                        raw_msg = await ws_incoming.get()
                        if raw_msg is None:
                            break
                        parsed = json.loads(raw_msg)
                        human_input_queues[uuid].put_nowait(
                            parsed.get("content", "confirmed")
                        )
                        break  # Only one reply needed per HumanAgent call

                async for response in responses:
                    role = response.get("role", "")
                    content = response.get("content", "")
                    status = response.get("status", "")

                    if {"role", "content"}.issubset(response):
                        agent_message = {"role": role, "content": content}

                        # Detect HumanAgent prompt: the flow sends the prompt
                        # as a Cat Service Flow message right before waiting.
                        # We flag it so the UI knows to show an input field.
                        if "confirm" in content.lower() and (
                            "Tech Confirmation" in role
                            or "Tech Confirmation" in content
                        ):
                            agent_message["awaiting_input"] = True
                            # Start relay so user's reply reaches the executor
                            human_relay_active = True
                            relay_task = asyncio.create_task(human_relay())

                        await websocket.send_text(
                            f"JSONSTART{json.dumps(agent_message)}JSONEND"
                        )

                        print(f"{role}: {content[:120]}\n")

            print("\n\n")
    except WebSocketDisconnect:
        print(f"WebSocket disconnected: {uuid}")
    finally:
        reader_task.cancel()
        human_input_queues.pop(uuid, None)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app_ui:app", host="0.0.0.0", port=8000)
