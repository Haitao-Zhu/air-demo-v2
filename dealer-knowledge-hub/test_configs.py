"""
Test script for UC3 Dealer Knowledge Hub — tests each config step.
"""

import asyncio
import os
import sys
import uuid
import traceback

from air import AsyncAIRefinery
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

# Each test: (config_file, project_suffix, query, description, expected_agent, validation_keywords)
# validation_keywords: at least one must appear (OR logic) for a PASS
TESTS = [
    (
        "config_step1.yaml",
        "step1",
        "Which machines have more than 4000 hours?",
        "Step 1 — Fleet Analytics only",
        "Fleet Analytics",
        ["hours", "machine", "4,250", "4250", "6100", "7200"],
    ),
    (
        "config_step2.yaml",
        "step2",
        "Does CVA-Premium cover hydraulic pump replacement?",
        "Step 2 — Fleet Analytics + Warranty",
        "Warranty Policy Advisor",
        ["cva", "warranty", "premium", "coverage", "policy"],
    ),
    (
        "config_step3.yaml",
        "step3",
        "What are the specs of a Cat 320 GC?",
        "Step 3 — + Search + Planning",
        "Cat Equipment Search",
        ["search", "320", "spec", "cat"],
    ),
    (
        "config.yaml",
        "final",
        "List all machines with warranty expiring soon and recommend next steps",
        "Final config — full hub with decompose",
        None,  # multiple agents expected
        ["warranty", "machine", "expir"],
    ),
]


async def test_config(config_file: str, project_suffix: str, query: str,
                      description: str, expected_agent: str | None,
                      keywords: list[str]) -> tuple[bool, str]:
    """Deploy a config and send a test query. Returns (passed, detail)."""
    project_name = f"dkh_test_{project_suffix}"
    user_id = str(uuid.uuid4()).replace("-", "_")

    print(f"\n{'='*70}")
    print(f"TEST: {description}")
    print(f"  Config : {config_file}")
    print(f"  Project: {project_name}")
    print(f"  Query  : {query}")
    print(f"{'='*70}")

    try:
        # 1. Deploy / create the project with this config
        client = AsyncAIRefinery(api_key=api_key, base_url=base_url)
        print("  -> Creating project...")
        client.distiller.create_project(
            config_path=config_file,
            project=project_name,
        )
        print("  -> Project created OK")

        # 2. Send query
        print("  -> Sending query...")
        collected_responses = []
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
                    print(f"\n  [{agent}]")
                    # Truncate long responses for readability
                    preview = content[:500] + ("..." if len(content) > 500 else "")
                    print(f"  {preview}")

        if not collected_responses:
            return False, "No responses received"

        # 3. Check routing: did the expected agent respond?
        responding_agents = [a for a, _ in collected_responses]
        if expected_agent and expected_agent not in responding_agents:
            return False, (
                f"Expected agent '{expected_agent}' did not respond. "
                f"Got: {responding_agents}"
            )

        # 4. Keyword validation (OR logic — at least one keyword must appear)
        all_text = " ".join(c for _, c in collected_responses).lower()
        found = [kw for kw in keywords if kw.lower() in all_text]
        if not found:
            return False, f"Response matched none of expected keywords: {keywords}"

        detail = f"Agents: {responding_agents}, matched keywords: {found}"
        return True, detail

    except Exception as e:
        tb = traceback.format_exc()
        return False, f"Exception: {e}\n{tb}"


async def main():
    results = []
    for config_file, suffix, query, desc, expected_agent, keywords in TESTS:
        passed, detail = await test_config(config_file, suffix, query, desc,
                                           expected_agent, keywords)
        results.append((desc, passed, detail))

    # Summary
    print("\n" + "=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    all_pass = True
    for desc, passed, detail in results:
        status = "PASS" if passed else "FAIL"
        if not passed:
            all_pass = False
        print(f"  [{status}] {desc}")
        if not passed:
            print(f"         {detail}")

    print()
    if all_pass:
        print("All tests PASSED.")
    else:
        print("Some tests FAILED.")
    return 0 if all_pass else 1


if __name__ == "__main__":
    rc = asyncio.run(main())
    sys.exit(rc)
