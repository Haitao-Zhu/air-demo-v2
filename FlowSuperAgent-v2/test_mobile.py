"""Consistency test for mobile plan comparison flow.
Runs the same query 3 times and reports success/failure for each."""

import asyncio
import os
import uuid

from air import AsyncAIRefinery
from dotenv import load_dotenv

load_dotenv(override=True)

api_key = os.environ["API_KEY"]
base_url = os.environ.get("BASE_URL", "https://api.airefinery.accenture.com")

QUERY = "do the mobile plan compare workflow"
NUM_RUNS = 3


async def run_once(run_id: int):
    client = AsyncAIRefinery(api_key=api_key, base_url=base_url)
    client.distiller.create_project(
        config_path="config_mobile.yaml",
        project="mobile_plan_test",
    )

    user_id = f"test_{uuid.uuid4().hex[:8]}"
    results = {}
    success = True

    print(f"\n{'='*60}")
    print(f"  RUN {run_id}/{NUM_RUNS}")
    print(f"{'='*60}")

    async with client.distiller(
        project="mobile_plan_test",
        uuid=user_id,
    ) as dc:
        responses = await dc.query(query=QUERY)
        async for response in responses:
            if {"role", "content"}.issubset(response):
                agent = response["role"]
                content = response["content"]
                results[agent] = content

                # Check for failure patterns
                is_fail = any(phrase in content.lower() for phrase in [
                    "do not contain information relevant",
                    "failed to retrieve",
                    "no relevant information",
                    "could not find",
                ])

                status = "FAIL" if is_fail else "OK"
                if is_fail:
                    success = False

                print(f"\n[{status}] {agent}")
                print(f"  {content[:200]}...")

    return success


async def main():
    print("Mobile Plan Comparison — Consistency Test")
    print(f"Running query {NUM_RUNS} times: '{QUERY}'")

    results = []
    for i in range(1, NUM_RUNS + 1):
        try:
            ok = await run_once(i)
            results.append(ok)
        except Exception as e:
            print(f"\n[ERROR] Run {i} crashed: {e}")
            results.append(False)

    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for i, ok in enumerate(results, 1):
        print(f"  Run {i}: {'PASS' if ok else 'FAIL'}")
    passed = sum(results)
    print(f"\n  {passed}/{NUM_RUNS} passed ({passed/NUM_RUNS*100:.0f}% consistency)")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())
