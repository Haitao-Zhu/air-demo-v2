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
        executor_dict={"Detail Collector": terminal_input},
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
    print("Cat Safety & Compliance Advisor")
    print("=" * 50)
    print()
    print("Example queries by config step:")
    print()
    print("  Step 1 (Safety Protocol Advisor — UtilityAgent):")
    print('    "What PPE is required for operating a Cat 320 excavator near a highway?"')
    print('    "What is the emergency shutdown procedure for a Cat D8 dozer?"')
    print()
    print("  Step 2 (+ Incident Analyst — AnalyticsAgent):")
    print('    "How many incidents were Critical severity?"')
    print('    "Which site has the most safety incidents?"')
    print()
    print("  Step 3 (+ Regulation Searcher + Safety Doc Writer):")
    print('    "Write a toolbox talk about excavator swing radius safety"')
    print('    "What are the OSHA requirements for excavator operations near highways?"')
    print()
    print("  Full config (+ Incident Report Flow — FlowSuperAgent):")
    print('    "I need to report a safety incident"  (triggers full workflow with human input)')
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
