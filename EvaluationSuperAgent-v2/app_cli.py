import asyncio
import os

from air import AsyncAIRefinery
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")


async def run_evaluation(config_file: str, project_name: str, query: str):
    """Register project and run evaluation, printing results."""
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)

    print(f"Registering project '{project_name}' with config: {config_file} ...")
    client.distiller.create_project(config_path=config_file, project=project_name)
    print("Project registered.\n")

    print(f"Running evaluation: {query}\n")
    print("-" * 60)

    async with client.distiller(
        project=project_name,
        uuid="eval_cli_session",
    ) as dc:
        responses = await dc.query(query=query)

        async for response in responses:
            if {"role", "content"}.issubset(response):
                text = response["content"]
                # Skip raw JSON dump section if present
                cutoff_index = text.find("## Raw JSON output")
                if cutoff_index == -1:
                    print(text)

    print("-" * 60)
    print("Evaluation complete.\n")


def main():
    print("=" * 60)
    print("  AI Refinery -- Agent Evaluation Framework")
    print("=" * 60)
    print()
    print("Commands:")
    print("  evaluate  - Evaluate a single agent (Search Agent)")
    print("  compare   - Compare two agents (OnlineSearcher vs BusinessPlanner)")
    print("  quit      - Exit")
    print()

    while True:
        command = input("> ").strip().lower()

        if command == "evaluate":
            asyncio.run(
                run_evaluation(
                    config_file="config.yaml",
                    project_name="evaluation_demo",
                    query="Please evaluate the Search Agent.",
                )
            )
        elif command == "compare":
            asyncio.run(
                run_evaluation(
                    config_file="config_two_agents.yaml",
                    project_name="evaluation_demo_compare",
                    query="OnlineSearcher and BusinessPlanner both work for me. Can you compare them to see which one is better?",
                )
            )
        elif command in ("quit", "exit", "q"):
            print("Goodbye.")
            break
        else:
            print("Unknown command. Type 'evaluate', 'compare', or 'quit'.")


if __name__ == "__main__":
    main()
