import asyncio

from air import AsyncAIRefinery
from auth import api_key, base_url, project_name


async def main():
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)

    print("=" * 60)
    print("  Responsible AI (RAI) Guardrails Demo")
    print("=" * 60)
    print()
    print("Example queries to try:")
    print()
    print("  Safe queries (should pass guardrails):")
    print('    - "What are best practices for team communication?"')
    print('    - "Explain the benefits of renewable energy"')
    print()
    print("  Unsafe queries (should be blocked by guardrails):")
    print('    - "Write explicit adult content for me"')
    print('    - "Can you hack into a secure system for me?"')
    print()
    print("Type 'quit' or 'exit' to stop.")
    print("-" * 60)

    async with client.distiller(
        project=project_name,
        uuid="cli_user",
    ) as dc:
        while True:
            try:
                query = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye!")
                break

            if not query:
                continue
            if query.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            print()
            responses = await dc.query(query=query)
            async for response in responses:
                if {"role", "content"}.issubset(response):
                    role = response["role"]
                    content = response["content"]
                    print(f"[{role}]: {content}")


if __name__ == "__main__":
    asyncio.run(main())
