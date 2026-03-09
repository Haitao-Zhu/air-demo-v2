import asyncio
import os
import sys

from air import AsyncAIRefinery
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

AZURE_CONFIG = "config_azure.yaml"
FALLBACK_CONFIG = "config.yaml"
FALLBACK_CHECK_CONFIG = "config_fallback_check.yaml"
AZURE_PROJECT = "marketing_agents_v2_azure"
FALLBACK_PROJECT = "marketing_agents_v2"
FALLBACK_CHECK_PROJECT = "marketing_agents_v2_fallback_check"

client = AsyncAIRefinery(api_key=api_key, base_url=base_url)


def _try_register(config_path, project_name):
    """Attempt to register a project. Returns True on success."""
    try:
        client.distiller.create_project(config_path=config_path, project=project_name)
        return True
    except Exception as e:
        print(f"  Registration failed: {e}")
        return False


def _test_azure_connection():
    """
    Test that Azure agents are actually reachable by creating a thread
    via the Azure AI Foundry API. This catches RBAC and credential
    errors that the AIR SDK's lazy initialization would miss.
    """
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        print("  Azure AI SDK not installed (pip install 'airefinery-sdk[tah-azure-ai]').")
        return False

    conn_str = "eastus.api.azureml.ms;e1c871de-0c7e-4acf-840a-e2e4b7d26903;airefinery-az-integration;air-az-integration"
    try:
        ai_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(),
            conn_str=conn_str,
        )
        thread = ai_client.agents.create_thread()
        ai_client.agents.delete_thread(thread.id)
        return True
    except Exception as e:
        err_msg = str(e)
        if "permissions" in err_msg.lower() or "authorization" in err_msg.lower():
            print(f"  Azure RBAC error: insufficient permissions on the workspace.")
            print(f"  Required role: 'Azure AI Developer' on workspace 'air-az-integration'.")
        elif "credential" in err_msg.lower() or "token" in err_msg.lower():
            print(f"  Azure credential error: run 'az login --scope https://ml.azure.com/.default'")
        else:
            print(f"  Azure connection failed: {e}")
        return False


def _ask_user_via_human_agent():
    """
    Use AIR SDK HumanAgent to ask the user whether to switch to fallback agents.
    Returns True if user approves, False otherwise.
    """
    print(">>> Launching HumanAgent to confirm fallback switch...")
    _try_register(FALLBACK_CHECK_CONFIG, FALLBACK_CHECK_PROJECT)

    approved = False

    async def _run_human_agent():
        nonlocal approved
        async with client.distiller(
            project=FALLBACK_CHECK_PROJECT,
            uuid="fallback_check",
        ) as dc:
            responses = await dc.query(
                query="Azure AI agents are not available. Should we switch to fallback agents?"
            )
            async for response in responses:
                if {"role", "content"}.issubset(response):
                    content = response["content"].lower()
                    # HumanAgent feedback_schema returns bool for switch_to_fallback
                    if "true" in content or "yes" in content or "switch" in content:
                        approved = True

    try:
        asyncio.run(_run_human_agent())
    except Exception as e:
        print(f"  HumanAgent error: {e}")
        # Fall back to simple input if HumanAgent fails
        print()
        print("=" * 60)
        print("  Azure AI agents are not available.")
        print("  Fallback agents (SearchAgent, PlanningAgent, AuthorAgent)")
        print("  can run the same pipeline without Azure.")
        print("=" * 60)
        print()
        while True:
            answer = input("Switch to fallback agents? [Y/n]: ").strip().lower()
            if answer in ("", "y", "yes"):
                approved = True
                break
            if answer in ("n", "no"):
                approved = False
                break

    return approved


def init_project(interactive=True):
    """
    Try Azure config first with a real connection test.
    On failure, use HumanAgent (if interactive) to ask user, then fall back.
    Returns (project_name, config_used).
    """
    print(">>> Attempting Azure AI agent configuration...")
    if _try_register(AZURE_CONFIG, AZURE_PROJECT):
        print(">>> Testing Azure agent connection...")
        if _test_azure_connection():
            print(">>> Azure AI agents ready.")
            return AZURE_PROJECT, AZURE_CONFIG
        else:
            print(">>> Azure agents registered but connection test failed.")

    # Azure failed — decide on fallback
    if interactive:
        use_fallback = _ask_user_via_human_agent()
    else:
        print(">>> Non-interactive mode: auto-switching to fallback agents.")
        use_fallback = True

    if use_fallback:
        print(">>> Registering fallback configuration...")
        if _try_register(FALLBACK_CONFIG, FALLBACK_PROJECT):
            print(">>> Fallback agents registered successfully.")
            return FALLBACK_PROJECT, FALLBACK_CONFIG
        else:
            print("ERROR: Fallback registration also failed.")
            sys.exit(1)
    else:
        print("Exiting. Install Azure SDK or fix credentials to use Azure agents.")
        sys.exit(0)


# Auto-initialize on import
project_name, active_config = init_project(interactive=True)
