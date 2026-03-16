"""CustomAgent demo — generates synthetic data using a local async function."""

import asyncio
import os

from air import AsyncAIRefinery
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

client = AsyncAIRefinery(api_key=api_key, base_url=base_url)


# --- Custom agent function (runs locally) ---
async def synthetic_data_agent(query: str, **kwargs) -> str:
    """Generate synthetic data to help answer the user's question."""
    prompt = f"""
    Your task is to generate synthetic data that can help answer the user question below.
    Do not mention that this is synthetic data.

    {query}
    """
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="openai/gpt-oss-120b",
    )
    return response.choices[0].message.content


# --- Register custom function ---
executor_dict = {
    "SyntheticDataGenerator": synthetic_data_agent,
}

# --- Register project ---
config_path = "config.yaml"
project_name = "custom_agent_demo"

client.distiller.create_project(config_path=config_path, project=project_name)


async def main():
    print("Custom Agent Demo — Synthetic Data Generator")
    print("=" * 50)
    print("Example queries:")
    print('  "Generate a dataset of 5 customers with name, email, and purchase history"')
    print('  "Create sample IoT sensor readings for a factory floor"')
    print()

    while True:
        query = input("Query (or 'quit'): ").strip()
        if query.lower() in ("quit", "exit", "q"):
            break
        if not query:
            continue

        print("\nProcessing...\n")
        async with client.distiller(
            project=project_name,
            uuid="test_user",
            executor_dict=executor_dict,
        ) as dc:
            responses = await dc.query(query=query)
            async for response in responses:
                if {"role", "content"}.issubset(response):
                    print(f"[{response['role']}]: {response['content']}\n")
        print()


if __name__ == "__main__":
    asyncio.run(main())
