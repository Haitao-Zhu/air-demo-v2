"""
Test script for UC4 Safety Compliance — config_step1 through config_step3.
Skips config.yaml (step4) since it has a HumanAgent requiring interactive input.
"""

import asyncio
import os
import sys
import uuid
import traceback

from dotenv import load_dotenv

# Load env from the safety-compliance directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(override=True)

from air import AsyncAIRefinery

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")
project_name = "cat_safety_compliance"

STEPS = [
    {
        "config": "config_step1.yaml",
        "label": "Step 1 — Safety Protocol Advisor only",
        "query": "What PPE is required for operating a Cat 320 excavator?",
    },
    {
        "config": "config_step2.yaml",
        "label": "Step 2 — + Incident Analyst",
        "query": "Show me incident trends by severity",
    },
    {
        "config": "config_step3.yaml",
        "label": "Step 3 — + Search + Doc Writer",
        "query": "Write a toolbox talk about excavator swing radius safety",
    },
]


async def test_step(step: dict) -> tuple[bool, str]:
    """Deploy config, send query, return (passed, detail)."""
    config_path = step["config"]
    label = step["label"]
    query = step["query"]

    print(f"\n{'='*70}")
    print(f"TESTING: {label}")
    print(f"  Config : {config_path}")
    print(f"  Query  : {query}")
    print(f"{'='*70}")

    # 1. Deploy the config
    try:
        client = AsyncAIRefinery(api_key=api_key, base_url=base_url)
        client.distiller.create_project(
            config_path=config_path,
            project=project_name,
        )
        print(f"  [OK] Project deployed with {config_path}")
    except Exception as e:
        msg = f"Deploy failed: {e}"
        print(f"  [FAIL] {msg}")
        traceback.print_exc()
        return False, msg

    # 2. Query
    user_id = str(uuid.uuid4()).replace("-", "_")
    collected_responses = []
    try:
        async with client.distiller(
            project=project_name,
            uuid=user_id,
        ) as dc:
            responses = await dc.query(query=query)
            async for response in responses:
                if {"role", "content"}.issubset(response):
                    agent = response["role"]
                    content = response["content"]
                    collected_responses.append((agent, content))
                    print(f"\n  --- {agent} ---")
                    # Truncate long responses for readability
                    preview = content[:500] + ("..." if len(content) > 500 else "")
                    print(f"  {preview}\n")
    except Exception as e:
        msg = f"Query failed: {e}"
        print(f"  [FAIL] {msg}")
        traceback.print_exc()
        return False, msg

    # 3. Evaluate
    if not collected_responses:
        msg = "No responses received"
        print(f"  [FAIL] {msg}")
        return False, msg

    # Check that we got meaningful content (not just empty strings)
    has_content = any(len(content.strip()) > 20 for _, content in collected_responses)
    if not has_content:
        msg = "Responses were empty or too short"
        print(f"  [FAIL] {msg}")
        return False, msg

    agents_seen = [agent for agent, _ in collected_responses]
    msg = f"Got {len(collected_responses)} response(s) from: {', '.join(agents_seen)}"
    print(f"  [OK] {msg}")
    return True, msg


async def main():
    results = []
    for step in STEPS:
        passed, detail = await test_step(step)
        results.append((step["label"], passed, detail))

    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    all_passed = True
    for label, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"  [{status}] {label}")
        print(f"         {detail}")

    print()
    if all_passed:
        print("All steps passed!")
    else:
        print("Some steps FAILED — see details above.")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
