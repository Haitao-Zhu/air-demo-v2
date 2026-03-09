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
    print("Salesforce Knowledge Agent")
    print("=" * 40)
    print("Example queries:")
    print('  "Show me the features, benefits, and use cases of Salesforce Agentforce and Data Cloud"')
    print('  "How do AgentForce and Data Cloud work together to enhance CRM processes?"')
    print('  "Show me the features related to AI-powered customer interactions"')
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
