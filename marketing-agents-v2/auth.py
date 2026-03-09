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


def _test_azure():
    """Test Azure by creating a thread. Returns True if RBAC is OK."""
    try:
        from azure.ai.projects import AIProjectClient
        from azure.identity import DefaultAzureCredential
    except ImportError:
        print("  Azure AI SDK not installed.")
        return False

    conn_str = "eastus.api.azureml.ms;e1c871de-0c7e-4acf-840a-e2e4b7d26903;airefinery-az-integration;air-az-integration"
    try:
        ai_client = AIProjectClient.from_connection_string(
            credential=DefaultAzureCredential(), conn_str=conn_str,
        )
        thread = ai_client.agents.create_thread()
        ai_client.agents.delete_thread(thread.id)
        return True
    except Exception as e:
        print(f"  Azure test failed: {e}")
        return False


def init_project():
    """Test Azure, use it if it works, otherwise fallback. No prompts."""
    print(">>> Testing Azure AI agents...")
    if _test_azure():
        print(">>> Azure AI agents available.")
        try:
            client.distiller.create_project(config_path=AZURE_CONFIG, project=AZURE_PROJECT)
            print(f">>> Using Azure agents (project: {AZURE_PROJECT})")
            return AZURE_PROJECT, AZURE_CONFIG
        except Exception as e:
            print(f"  Azure config registration failed: {e}")

    print(">>> Azure unavailable, switching to fallback agents.")
    try:
        client.distiller.create_project(config_path=FALLBACK_CONFIG, project=FALLBACK_PROJECT)
        print(f">>> Using fallback agents (project: {FALLBACK_PROJECT})")
        return FALLBACK_PROJECT, FALLBACK_CONFIG
    except Exception as e:
        print(f"ERROR: Fallback registration failed: {e}")
        sys.exit(1)


project_name, active_config = init_project()
