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
    print("Cat Dealer Knowledge Hub")
    print("=" * 50)
    print()
    print("Example queries by config step:")
    print()
    print("  Step 1 (Fleet Analytics — AnalyticsAgent):")
    print('    "Which machines have more than 4000 hours?"')
    print('    "Show overdue machines by customer"')
    print()
    print("  Step 2 (+ Warranty Policy Advisor — UtilityAgent):")
    print('    "Does CVA-Premium cover hydraulic pump replacement?"')
    print('    "Which machines have warranty expiring in 90 days?"')
    print()
    print("  Step 3 (+ Cat Equipment Search + Service Planner + decompose):")
    print('    "Create a maintenance plan for Turner Construction\'s fleet"')
    print()
    print("  Full config (all 4 agents in one query):")
    print('    "Full fleet review for Turner: list all machines with hours and service')
    print('     status, check warranty coverage, look up Cat 320 GC specs, and create a service plan"')
    print()
    print("  Multi-part (decompose):")
    print('    "List all machines with warranty expiring in 90 days and recommend a CVA upgrade plan"')
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
