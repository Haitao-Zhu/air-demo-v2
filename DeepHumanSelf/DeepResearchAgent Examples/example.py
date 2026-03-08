import asyncio
import os

from utils import handle_dra_message

from air import DistillerClient
from air.utils import async_print

# Authenticate using environment variables or fallback values.
BASE_URL = os.getenv("AIREFINERY_ADDRESS", "https://api.airefinery.accenture.com")
API_KEY = os.getenv("API_KEY", "")


async def deep_research_test():
    """
    Deep Research Agent testing with different configurations.

    Reports will be saved to report_output/<config_name>/ in multiple formats
    (Markdown, HTML) based on the additional_output_formats config.
    """
    config_files = [
        (
            "balanced.yaml",
            "What are the main competitive advantages of Accenture in the overall AI market?",
        ),
        (
            "exploratory.yaml",
            "What are the major trends shaping the future of generative AI across different industries?",
        ),
        (
            "focused.yaml",
            "How is Accenture applying AI internally to improve operational efficiency?",
        ),
    ]

    for config_path, query in config_files:
        print(f"\n=== Running config: {config_path} ===")
        project_name = f"deep_research_{config_path.split('.', maxsplit=1)[0]}"

        # Create project using this config
        distiller_client = DistillerClient(api_key=API_KEY, base_url=BASE_URL)
        distiller_client.create_project(config_path=config_path, project=project_name)

        async with distiller_client(project=project_name, uuid="test_user") as dc:
            responses = await dc.query(query=query)
            print(f"----\nQuery: {query}")
            config_name = config_path.split(".", maxsplit=1)[0]
            async for response in responses:
                await handle_dra_message(
                    response,
                    audio_output_prefix=f"audio_output/{config_name}",
                    output_dir=f"report_output/{config_name}",
                )
            await dc.reset_memory()
            await async_print("Memory reset complete.")


if __name__ == "__main__":
    print("\nDeep Research Testing")
    asyncio.run(deep_research_test())
