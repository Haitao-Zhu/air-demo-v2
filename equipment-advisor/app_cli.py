import asyncio
import uuid

from air import AsyncAIRefinery

from auth import api_key, base_url, project_name


async def get_response(query: str, user_id: str):
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)
    async with client.distiller(
        project=project_name,
        uuid=user_id,
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
    print("Cat Equipment Advisor")
    print("=" * 50)
    print()
    print("Example queries by config step:")
    print()
    print("  Step 1 (Equipment Advisor — PlanningAgent):")
    print('    "What are the key differences between Cat 320 and Cat 336 excavators?"')
    print('    "Recommend a Cat dozer for a highway grading project"')
    print()
    print("  Step 2 (+ Equipment Analyst — CriticalThinker + SearchAgent):")
    print('    "Compare Cat D6 vs D8 for highway grading in Arizona"')
    print()
    print("  Step 3 (+ Report Formatter — AuthorAgent):")
    print('    "Create an equipment recommendation report for a construction company"')
    print()
    print("  Full config (+ Guardrails — UtilityAgent):")
    print('    "How does the Komatsu PC200 compare to the Cat 320?"')
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
