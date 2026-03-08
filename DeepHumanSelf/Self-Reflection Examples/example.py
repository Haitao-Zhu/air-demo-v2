# pylint: disable=duplicate-code
import asyncio
import os

from air import DistillerClient
from air.utils import async_print

# Authenticate using environment variables or fallback values.
BASE_URL = os.getenv("AIREFINERY_ADDRESS", "https://api.airefinery.accenture.com")
API_KEY = os.getenv("API_KEY", "")
SELF_REFLECTION_PROJECT_NAME = "search_agent_self_reflection"
WITHOUT_SELF_REFLECTION_PROJECT_NAME = "search_agent_without_self_reflection"


async def search_agent_self_reflection_demo():  # pylint: disable=missing-function-docstring
    distiller_client = DistillerClient(base_url=BASE_URL, api_key=API_KEY)

    distiller_client.create_project(
        config_path="self_reflection.yaml", project=SELF_REFLECTION_PROJECT_NAME
    )
    distiller_client.create_project(
        config_path="self_reflection_disabled.yaml",
        project=WITHOUT_SELF_REFLECTION_PROJECT_NAME,
    )

    custom_agent_gallery = {}
    # pylint: disable-line-too-long
    queries = [
        "What is the name of the college where Prine Nirajan Bir Bikram Shah Dev completed his bachelor's degree?",  # Kathmandu College of Management.
        "In which specific issue did Black Condor II perish?",  # Infinite Crisis #1
        "Who lived longer, Leonid Khachiyan or Nikolai Lobachevsky?",  # Nikolai Lobachevsky
        "On what date, month, and year was the Jonas Mekas Visual Arts Center opened by avant-garde filmmaker Jonas Mekas with its premiere exhibition entitled 'The Avant-Garde: From Futurism to Fluxus'?",  # November 10, 2007
        "On what day, month, and year did the Brazilian mathematician Leopoldo Luis Cabo Penna Franca marry Ana Cristina Leonardos?",  # 7/28/1983
    ]

    for query in queries:
        print(f"\n==== Query ====\n{query}")

        async with distiller_client(
            project=WITHOUT_SELF_REFLECTION_PROJECT_NAME,
            uuid="test_user",
            custom_agent_gallery=custom_agent_gallery,
        ) as dc_noreflect:
            result_noreflection = await dc_noreflect.query(query=query)
            noreflection_response = ""
            async for response in result_noreflection:
                noreflection_response += response["content"] + "\n"

        print("\n-- Without Self-Reflection --")
        print(noreflection_response)

        async with distiller_client(
            project=SELF_REFLECTION_PROJECT_NAME,
            uuid="test_user",
            custom_agent_gallery=custom_agent_gallery,
        ) as dc_reflect:
            result_reflection = await dc_reflect.query(query=query)
            reflection_response = ""
            async for response in result_reflection:
                reflection_response += response["content"] + "\n"

        print("\n-- With Self-Reflection --")
        print(reflection_response)

    # Reset memory
    async with distiller_client(
        project=SELF_REFLECTION_PROJECT_NAME,
        uuid="test_user",
        custom_agent_gallery=custom_agent_gallery,
    ) as dc_reflect:
        await dc_reflect.reset_memory()
        await async_print("Memory reset complete.")

    async with distiller_client(
        project=WITHOUT_SELF_REFLECTION_PROJECT_NAME,
        uuid="test_user",
        custom_agent_gallery=custom_agent_gallery,
    ) as dc_noreflect:
        await dc_noreflect.reset_memory()
        await async_print("Memory reset complete.")


def interactive():
    """
    Runs an interactive session using DistillerClient.
    """
    distiller_client = DistillerClient(base_url=BASE_URL, api_key=API_KEY)
    distiller_client.create_project(
        config_path="self_reflection.yaml", project=SELF_REFLECTION_PROJECT_NAME
    )
    distiller_client.interactive(
        project=SELF_REFLECTION_PROJECT_NAME,
        uuid="test_user",
        custom_agent_gallery={},
    )


if __name__ == "__main__":
    print("\nSearch Agent (Self-Reflection vs. Baseline) Demo")
    asyncio.run(search_agent_self_reflection_demo())

    print(
        "\nInteractive Mode (Self-reflection)\nTo trigger the corresponding agents with self-reflection, you can include the agent name (e.g., 'Search Agent') in your query."
    )
    interactive()
