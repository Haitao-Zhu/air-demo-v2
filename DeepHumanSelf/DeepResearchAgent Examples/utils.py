import base64
import json
from pathlib import Path
from typing import Optional

from pydantic import TypeAdapter
from tqdm import tqdm

from air.types.distiller.client import DistillerIncomingMessage
from air.types.distiller.deep_research import (
    DeepResearchIRProgressPayload,
    DeepResearchIRQuestionDonePayload,
    DeepResearchPayloadType,
    DeepResearchPipelineStepPayload,
    DeepResearchReferencePayload,
    DeepResearchResearchQuestionsPayload,
    DeepResearchStatus,
    DeepResearchStep,
    DeepResearchSummaryStatisticsPayload,
    DeepResearchThoughtStatusPayload,
)

# =============================================================================
# Constants
# =============================================================================

OUTPUT_FORMAT_EXTENSIONS = {
    "html": ".html",
    "docx": ".docx",
}

STEP_EMOJIS = {
    DeepResearchStep.START_FOLLOW_UP: "🔍 ",
    DeepResearchStep.END_FOLLOW_UP_POS: "🧑 ",
    DeepResearchStep.START_QUERY_REWRITER: "📝 ",
    DeepResearchStep.START_SEARCH_BACKGROUND: "🔎 ",
    DeepResearchStep.FAIL_SEARCH_BACKGROUND: "❌ ",
    DeepResearchStep.FAIL_CLARIFICATION: "❗️ ",
    DeepResearchStep.START_RESEARCH_PLANNER: "🗂️" + " ",
    DeepResearchStep.FAIL_RESEARCH_PLANNER: "❌ ",
    DeepResearchStep.START_ITERATIVE_RESEARCH: "🔄 ",
    DeepResearchStep.ITERATIVE_RESEARCH_TASK_FAILED: "⚠️ ",
    DeepResearchStep.ITERATIVE_RESEARCH_PIPELINE_ABORTED: "❌ ",
    DeepResearchStep.START_AUTHOR: "🧾 ",
    DeepResearchStep.END_AUTHOR: "✅ ",
    DeepResearchStep.FAIL_AUTHOR: "❌ ",
    DeepResearchStep.START_AUDIO: "🔊 ",
    DeepResearchStep.FAIL_AUDIO: "❌ ",
    DeepResearchStep.START_RENDER_REPORT: "📄 ",
    DeepResearchStep.END_RENDER_REPORT: "✅ ",
    DeepResearchStep.FAIL_PARTIAL_RENDER_REPORT: "⚠️ ",
    DeepResearchStep.FAIL_ALL_RENDER_REPORT: "❌ ",
}

# =============================================================================
# File I/O Utilities
# =============================================================================


def save_base64_file(base64_content: str, output_path: str) -> None:
    """Save base64-encoded content to a file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    decoded_bytes = base64.b64decode(base64_content)
    with open(output_path, "wb") as f:
        f.write(decoded_bytes)
    print(f"Saved: {output_path}")


def _save_audio(
    content: str,
    audio_output_prefix: str,
    audio_file_ext: str,
    metadata: dict,
) -> None:
    """Save audio file and optional transcription."""
    audio_path = f"{audio_output_prefix}{audio_file_ext}"
    save_base64_file(content, audio_path)

    transcription = metadata.get("transcription")
    if transcription:
        transcription_path = f"{audio_output_prefix}.txt"
        with open(transcription_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        print(f"Saved transcription to {transcription_path}")


# =============================================================================
# Display Utilities
# =============================================================================


def _print_progress_bar(processed_tasks: int, total_task: int, title: str) -> None:
    """Display a progress bar using tqdm."""
    denom = max(total_task, 1)
    pct = int(round((processed_tasks / denom) * 100))
    pct = max(0, min(100, pct))

    pbar = tqdm(
        total=100,
        desc=title,
        bar_format="{l_bar}{bar} | {n_fmt}/{total_fmt}",
    )
    pbar.n = pct
    pbar.refresh()
    pbar.close()


def _print_reference_message(
    ref_payload: DeepResearchReferencePayload, action_verb: str = "Searching"
) -> None:
    """Print reference URLs for a research question."""
    urls = list(ref_payload.references.keys())
    bullet_list = "\n".join(f"- {url}" for url in urls)
    print(
        f"\n[Research Question {ref_payload.question_id}] {action_verb} "
        f"{len(urls)} source{'s' if len(urls) != 1 else ''}:\n{bullet_list}\n"
    )


# =============================================================================
# Payload Handlers
# =============================================================================


def _handle_typed_payload(status: str, payload) -> None:
    """Handle known typed payloads."""
    if status == DeepResearchStatus.IR_PROGRESS and isinstance(
        payload, DeepResearchIRProgressPayload
    ):
        _print_progress_bar(
            processed_tasks=payload.processed_tasks,
            total_task=payload.total_task,
            title="Research Progress",
        )

    elif status == DeepResearchStatus.REFERENCE and isinstance(
        payload, DeepResearchReferencePayload
    ):
        _print_reference_message(payload)

    elif status == DeepResearchStatus.RESEARCH_QUESTIONS and isinstance(
        payload, DeepResearchResearchQuestionsPayload
    ):
        print("\nGenerated research questions:")
        for q in payload.questions:
            print(f"- {q}")
        print("")

    elif status == DeepResearchStatus.THOUGHT_STATUS and isinstance(
        payload, DeepResearchThoughtStatusPayload
    ):
        print(f"\n[Research Question {payload.question_id}] {payload.thought}\n")

    elif status == DeepResearchStatus.SUMMARY_STATISTICS and isinstance(
        payload, DeepResearchSummaryStatisticsPayload
    ):
        print(
            f"\n⏰ The Deep Research Agent ran for a total of {payload.used_time:.2f} "
            f"minutes, and searched {payload.website_num} websites.\n"
        )

    # Granular per-question completion signal (new dedicated status)
    elif status == DeepResearchStatus.IR_QUESTION_DONE and isinstance(
        payload, DeepResearchIRQuestionDonePayload
    ):
        status_label = "✅ Done" if payload.status == "done" else "❌ Failed"
        # Show the message whenever present, regardless of status
        suffix = f": {payload.message}" if payload.message else ""
        print(f"\n[Research Question {payload.question_id}] {status_label}{suffix}\n")

    elif status == DeepResearchStatus.PIPELINE_STEP and isinstance(
        payload, DeepResearchPipelineStepPayload
    ):
        emoji = STEP_EMOJIS.get(payload.step_key, "")
        print(f"\n{emoji}{payload.info}\n")

    else:
        print(f"\n[Unhandled payload] status={status}, payload={payload}\n")


# =============================================================================
# Main function
# =============================================================================


async def handle_dra_message(
    response: DistillerIncomingMessage,
    audio_output_prefix: str,
    audio_file_ext: str = ".mp3",
    output_dir: Optional[str] = None,
) -> None:
    """
    Handle and print a server Message dict.

    Args:
        response: The incoming message from the distiller.
        audio_output_prefix: Prefix path for audio output files.
        audio_file_ext: Extension for audio files (default: ".mp3").
        output_dir: Directory to save report outputs (HTML, Word).
                   If None, report format outputs are not saved.
    """
    # Extract basic fields from the incoming message
    status = response.get("status", "")
    content = response.get("content", "")

    # Attempt to parse the content as a typed DeepResearch payload
    payload = None
    if content:
        try:
            payload_adapter = TypeAdapter(DeepResearchPayloadType)
            payload = payload_adapter.validate_python(json.loads(content))
        except Exception:
            pass

    # Handle structured (typed) DeepResearch payloads
    if payload:
        _handle_typed_payload(status, payload)
        return

    # Handle output format messages (html, docx)
    if status in OUTPUT_FORMAT_EXTENSIONS:
        if output_dir and content:
            ext = OUTPUT_FORMAT_EXTENSIONS[status]
            save_base64_file(content, f"{output_dir}/report{ext}")
        elif not output_dir:
            print(f"[{status}] Report format received but output_dir not specified")
        return

    # Handle audio output
    if status == "audio" and content:
        _save_audio(
            content, audio_output_prefix, audio_file_ext, response.get("metadata", {})
        )
        return

    # Fallback: print content or status
    if content:
        print(f"\n{content}\n")
    elif status:
        print(f"[{status}] {response}")
    else:
        print(f"[Unknown message] {response}")
