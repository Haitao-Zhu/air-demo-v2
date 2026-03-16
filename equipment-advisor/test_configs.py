"""Test all UC1 config steps for consistency."""
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

PROJECT_NAME = "uc1_equipment_test"

TESTS = [
    {
        "config": "config_step1.yaml",
        "label": "Step 1 — Single PlanningAgent",
        "query": "What are the key differences between Cat 320 and Cat 336 excavators?",
    },
    {
        "config": "config_step2.yaml",
        "label": "Step 2 — Search + CriticalThinker",
        "query": "Compare Cat D6 vs D8 for highway grading in Arizona",
    },
    {
        "config": "config_step3.yaml",
        "label": "Step 3 — Search + Analyst + Report",
        "query": "Create an equipment recommendation for a construction company looking at excavators",
    },
    {
        "config": "config.yaml",
        "label": "Step 4 (Final) — Full with Guardrails",
        "query": "How does the Cat 320 compare for general construction use?",
    },
]

PER_TEST_TIMEOUT = 180


async def _run_query(config_path: str, user_id: str, query: str) -> list:
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)
    client.distiller.create_project(config_path=config_path, project=PROJECT_NAME)

    collected = []
    async with client.distiller(project=PROJECT_NAME, uuid=user_id) as dc:
        responses = await dc.query(query=query)
        async for response in responses:
            if {"role", "content"}.issubset(response):
                collected.append({
                    "agent": response["role"],
                    "content": response["content"],
                })
    return collected


async def test_config(test: dict) -> dict:
    result = {"label": test["label"], "status": "FAIL"}
    user_id = f"test_{uuid.uuid4().hex[:8]}"

    try:
        collected = await asyncio.wait_for(
            _run_query(test["config"], user_id, test["query"]),
            timeout=PER_TEST_TIMEOUT,
        )

        if not collected:
            result["reason"] = "No responses received"
            return result

        fail_phrases = ["unable to handle", "do not contain information", "failed to retrieve"]
        last_content = collected[-1]["content"]
        is_fail = any(p in last_content.lower() for p in fail_phrases)

        if is_fail:
            result["reason"] = f"Agent returned failure: {last_content[:100]}"
            return result

        result["status"] = "PASS"
        result["agents"] = [r["agent"] for r in collected[:6]]
        result["snippet"] = last_content[:150]

    except Exception as e:
        result["reason"] = f"{type(e).__name__}: {e}"

    return result


async def main():
    print("UC1 Equipment Advisor — Config Test")
    print("=" * 60)

    results = []
    for test in TESTS:
        print(f"\nTesting: {test['label']}")
        print(f"  Config: {test['config']}")
        print(f"  Query:  {test['query']}")

        r = await test_config(test)
        results.append(r)

        if r["status"] == "PASS":
            print(f"  Result: PASS")
            print(f"  Agents: {', '.join(r.get('agents', []))}")
            print(f"  Snippet: {r.get('snippet', '')[:120]}...")
        else:
            print(f"  Result: FAIL — {r.get('reason', 'unknown')}")

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(1 for r in results if r["status"] == "PASS")
    for r in results:
        print(f"  [{'PASS' if r['status'] == 'PASS' else 'FAIL'}] {r['label']}")
    print(f"\n  {passed}/{len(results)} passed")

    if passed < len(results):
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
