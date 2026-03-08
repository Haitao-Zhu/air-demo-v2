import asyncio
import os
import sys

from air import DistillerClient
from air.utils import async_print


BASE_URL = os.getenv("AIREFINERY_ADDRESS", "https://api.airefinery.accenture.com")
API_KEY = os.getenv("API_KEY", "Cf7AIvdcT5-ZpEsN_BmGjeQMbrVsI03h-v0mUJPpLxY=")


async def custom_input_method_from_file(query: str) -> str:
    """
    Custom input method that reads user feedback from a file.
    Used in demo3 to simulate user feedback collection.
    """
    loop = asyncio.get_running_loop()

    def read_file():
        if not os.path.exists("custom_dummy_response.txt"):
            return "[No input found]"
        with open("custom_dummy_response.txt", "r", encoding="utf-8") as file:
            return file.read()

    return await loop.run_in_executor(None, read_file)


async def run_demo(project_name: str, config_path: str, query: str, executor_dict=None):
    """
    Generic runner for a human-in-the-loop demo.
    """
    client = DistillerClient(base_url=BASE_URL, api_key=API_KEY)
    session_uuid = f"session_{os.getpid()}"

    client.create_project(config_path=config_path, project=project_name)

    async with client(
        project=project_name, uuid=session_uuid, executor_dict=executor_dict
    ) as dc:
        print(f"--- Running Query: {query} ---")
        responses = await dc.query(query=query)

        async for response in responses:
            await async_print(
                f"Response from {response['role']}: {response['content']}"
            )

        await dc.reset_memory()
        await async_print("--- Session Complete ---")


async def main():
    if len(sys.argv) != 2 or sys.argv[1] not in {"demo1", "demo2", "demo3"}:
        print("Usage: python example.py [demo1|demo2|demo3]")
        return

    demo = sys.argv[1]

    if demo == "demo1":
        # Demo 1: Interactive Research Loop
        # Scenario: User researches a topic, gives live feedback, and the system refines the result.
        # Query preparation: Structure Mode - Defined by a feedback schema.
        # Feedback collection: Terminal - User enters responses via the terminal.
        await run_demo(
            project_name="human_in_the_loop_project",
            config_path="human_in_the_loop.yaml",
            query="What are the latest advancements in LLMs?",
        )

    elif demo == "demo2":
        # Demo 2: Interactive Dinner Planner Loop
        # Scenario: User requests a dinner plan; system gathers feedback and improves suggestions.
        # Query preparation: Free-form Mode - Prepared by upstream agent.
        # Feedback collection: Terminal - User enters responses via the terminal.
        await run_demo(
            project_name="human_in_the_loop_project",
            config_path="planner.yaml",
            query="What should I make for weekend dinner?",
        )

    elif demo == "demo3":
        # Demo 3: Interactive Research Loop with Custom Input
        # Scenario: User feedback is loaded from a file instead of typed live, useful for automated pipelines.
        # Query preparation: Structure Mode - Defined by a feedback schema.
        # Feedback collection: Custom - User response is read by files.
        await run_demo(
            project_name="human_in_the_loop_project",
            config_path="custom_example.yaml",
            query="What are the latest advancements in LLMs?",
            executor_dict={"Human Reviewer": custom_input_method_from_file},
            # Add executor_dict, the agent name should be consistent as defined in the yaml file
        )


if __name__ == "__main__":
    asyncio.run(main())
