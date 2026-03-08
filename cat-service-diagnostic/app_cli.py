import asyncio
import sys
import uuid

from air import AsyncAIRefinery

from auth import api_key, base_url, project_name


async def terminal_input(query: str) -> str:
    """Async terminal input for HumanAgent Custom mode."""
    loop = asyncio.get_running_loop()
    print(query, end="", flush=True)
    fut = loop.create_future()

    def on_ready():
        if fut.done():
            return
        fut.set_result(sys.stdin.readline().rstrip("\n"))

    loop.add_reader(sys.stdin, on_ready)
    try:
        return await fut
    finally:
        loop.remove_reader(sys.stdin)


async def get_response(query: str, user_id: str):
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)
    async with client.distiller(
        project=project_name,
        uuid=user_id,
        executor_dict={"Tech Confirmation": terminal_input},
    ) as dc:
        responses = await dc.query(query=query)
        async for response in responses:
            if {"role", "content"}.issubset(response):
                agent = response["role"]
                content = response["content"]
                print(f"\n--- {agent} ---")
                print(f"{content}\n")


def main():
    user_id = str(uuid.uuid4()).replace("-", "_")
    print("Cat Service Diagnostic Flow")
    print("=" * 40)
    print("Example queries:")
    print('  "Fault code E101-3 on a Cat 320, engine misfiring"  (Critical → tech confirmation)')
    print('  "Fault code E102-1 on a Cat 330"                    (Warning → auto flow)')
    print()

    while True:
        try:
            query = input("Query: ")
            if not query.strip():
                continue
            print("Sending query to AI Refinery...")
            asyncio.run(get_response(query, user_id))
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break


if __name__ == "__main__":
    main()
