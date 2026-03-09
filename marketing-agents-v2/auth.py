import os
import sys

from air import AsyncAIRefinery
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

AZURE_CONFIG = "config_azure.yaml"
FALLBACK_CONFIG = "config.yaml"
AZURE_PROJECT = "marketing_agents_v2_azure"
FALLBACK_PROJECT = "marketing_agents_v2"

client = AsyncAIRefinery(api_key=api_key, base_url=base_url)


def _try_register(config_path, project_name):
    """Attempt to register a project. Returns True on success."""
    try:
        client.distiller.create_project(config_path=config_path, project=project_name)
        return True
    except Exception as e:
        print(f"  Registration failed: {e}")
        return False


def _prompt_fallback():
    """Ask user whether to switch to fallback agents."""
    print()
    print("=" * 60)
    print("  Azure AI agents are not available.")
    print("  This may be due to missing Azure SDK, expired credentials,")
    print("  or insufficient permissions on the Azure workspace.")
    print()
    print("  Fallback agents (SearchAgent, PlanningAgent, AuthorAgent)")
    print("  can run the same pipeline without Azure.")
    print("=" * 60)
    print()
    while True:
        answer = input("Switch to fallback agents? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            return True
        if answer in ("n", "no"):
            return False


def init_project(interactive=True):
    """
    Try Azure config first. On failure, prompt user (if interactive)
    and fall back to non-Azure config.
    Returns (project_name, config_used).
    """
    # Try Azure
    print(">>> Attempting Azure AI agent configuration...")
    if _try_register(AZURE_CONFIG, AZURE_PROJECT):
        # Test that Azure SDK is importable (client-side executor requirement)
        try:
            from azure.ai.projects import AIProjectClient  # noqa: F401
            print(">>> Azure AI agents registered successfully.")
            return AZURE_PROJECT, AZURE_CONFIG
        except ImportError:
            print("  Azure AI SDK not installed (airefinery-sdk[tah-azure-ai]).")

    # Azure failed — decide on fallback
    if interactive:
        use_fallback = _prompt_fallback()
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
