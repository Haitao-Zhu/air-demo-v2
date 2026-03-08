import os

from air import AsyncAIRefinery
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

config_path = "config.yaml"
project_name = "flow_super_agent_demo"

client = AsyncAIRefinery(api_key=api_key, base_url=base_url)

client.distiller.create_project(
    config_path=config_path,
    project=project_name,
)
