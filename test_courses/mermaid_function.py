import asyncio
import logging
import uuid
from base64 import b64encode
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from dotenv import load_dotenv
from google import genai
from google.genai import types as genai_types
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)

# SUPPRIMER le client global (il garde un httpx async client lié à une boucle fermée)
# client = genai.Client()

PROJECT_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PROJECT_ROOT.parent
MERMAID_SERVER_PATH = REPO_ROOT / "mcp-mermaid" / "build" / "index.js"
OUTPUT_DIR = PROJECT_ROOT / "img"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
logger.debug("Mermaid OUTPUT_DIR resolved to: %s", OUTPUT_DIR)

if not MERMAID_SERVER_PATH.exists():
    logger.error("Mermaid server binary introuvable: %s", MERMAID_SERVER_PATH)

server_params = StdioServerParameters(
    command="node",
    args=[str(MERMAID_SERVER_PATH)],
    env={"NODE_ENV": "production"},
    cwd=str(MERMAID_SERVER_PATH.parent),
)

logger.info(
    "Configured MCP Mermaid server command: %s %s",
    server_params.command,
    server_params.args,
)


def _coerce_to_native(value: Any) -> Any:
    if isinstance(value, (str, bytes, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return value
    if isinstance(value, (list, tuple)):
        return list(value)
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()
    return value


def _extract_svg_contents(function_response: Dict[str, Any]) -> List[str]:
    def _collect_from(node: Any, results: List[str]) -> None:
        native = _coerce_to_native(node)
        if isinstance(native, dict):
            if native.get("type") == "text":
                text = native.get("text")
                if isinstance(text, str) and text.lstrip().startswith("<svg"):
                    results.append(text)
            content = native.get("content")
            if isinstance(content, Sequence) and not isinstance(
                content, (str, bytes, bytearray)
            ):
                for item in content:
                    _collect_from(item, results)
            for key in ("result", "response", "data"):
                if key in native:
                    _collect_from(native[key], results)
        elif isinstance(native, Sequence) and not isinstance(
            native, (str, bytes, bytearray)
        ):
            for entry in native:
                _collect_from(entry, results)

    collected: List[str] = []
    _collect_from(function_response, collected)
    return collected


def _iter_function_responses(
    node: Any, source: str
) -> Iterable[Tuple[str, Dict[str, Any]]]:
    native = _coerce_to_native(node)
    if isinstance(native, dict):
        if native.get("name") == "generate_mermaid_diagram":
            payload = native.get("response") or native
            yield source, _coerce_to_native(payload)
        for key in ("function_response", "parts", "response", "result", "content"):
            if key in native:
                yield from _iter_function_responses(native[key], source)
    elif isinstance(native, Sequence) and not isinstance(
        native, (str, bytes, bytearray)
    ):
        for item in native:
            yield from _iter_function_responses(item, source)


def _iter_mermaid_payloads(response: Any) -> Iterable[Tuple[str, Dict[str, Any]]]:
    candidates = getattr(response, "candidates", []) or []
    for cand_idx, candidate in enumerate(candidates):
        content = getattr(candidate, "content", None)
        parts = getattr(content, "parts", []) if content else []
        for part_idx, part in enumerate(parts or []):
            logger.debug(
                "Inspecting candidate %d part %d: %s", cand_idx, part_idx, part
            )
            func_call = getattr(part, "function_call", None)
            if func_call:
                logger.info(
                    "Found function_call in candidate %d part %d: %s",
                    cand_idx,
                    part_idx,
                    func_call,
                )
            function_response = getattr(part, "function_response", None)
            if function_response:
                yield from _iter_function_responses(
                    function_response, f"candidate[{cand_idx}].part[{part_idx}]"
                )

    extra_responses = getattr(response, "function_call_responses", []) or []
    if extra_responses:
        logger.info("Processing %d function_call_responses", len(extra_responses))
    for idx, func_resp in enumerate(extra_responses):
        yield from _iter_function_responses(
            func_resp, f"function_call_responses[{idx}]"
        )

    history = getattr(response, "automatic_function_calling_history", []) or []
    if history:
        logger.info(
            "Inspecting automatic function calling history with %d entries",
            len(history),
        )
    for turn_idx, turn in enumerate(history):
        yield from _iter_function_responses(turn, f"afc_history[{turn_idx}]")


def _save_svg(svg_text: str, prefix: str = "mermaid_genai") -> Path:
    unique_id = uuid.uuid4().hex
    target_path = OUTPUT_DIR / f"{prefix}_{unique_id}.svg"
    with open(target_path, "w", encoding="utf-8") as fp:
        fp.write(svg_text)
    logger.info("Saved SVG to %s", target_path)
    return target_path


async def run_mermaid_prompt(prompt: str) -> List[str]:
    if not MERMAID_SERVER_PATH.exists():
        logger.error("Mermaid server path introuvable: %s", MERMAID_SERVER_PATH)
        return []
    logger.info("Launching mermaid prompt run (prompt_len=%d)", len(prompt))
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            logger.info("Session initialized with MCP server")
            await session.initialize()

            try:
                # Créer un client async lié à la boucle courante (et le fermer proprement)
                async with genai.Client().aio as aio_client:
                    response = await aio_client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=genai_types.Content(
                            role="user",
                            parts=[genai_types.Part(text=prompt)],
                        ),
                        config=genai_types.GenerateContentConfig(
                            temperature=0,
                            tools=[session],
                        ),
                    )
            except Exception as e:
                logger.error("Error during generate_content: %s", e, exc_info=True)
                return []

            logger.info("Model responded; parsing tool outputs")
            try:
                logger.debug("Full response dump: %s", response.model_dump())
            except Exception:
                logger.debug("Response repr: %s", response)

            saved_paths: List[Path] = []
            encoded_svgs: List[str] = []
            for origin, payload in _iter_mermaid_payloads(response):
                logger.info("Detected generate_mermaid_diagram response via %s", origin)
                logger.debug("Payload aperçu: %s", str(payload)[:500])
                for svg_text in _extract_svg_contents(payload):
                    saved_paths.append(_save_svg(svg_text))
                    encoded_svgs.append(
                        b64encode(svg_text.encode("utf-8")).decode("ascii")
                    )

            final_text = response.text or ""
            if final_text:
                logger.info("Model textual response:\n%s", final_text)
            if saved_paths:
                logger.info("SVG files saved: %s", saved_paths)
            else:
                logger.warning("No SVG output detected in tool responses.")

            logger.debug("Nombre total de diagrammes encodés: %d", len(encoded_svgs))

        return encoded_svgs

    return []


def build_mermaid_prompt() -> str:
    return (
        "Generate two separate Mermaid flowcharts: one for the basic HTTP request lifecycle, "
        "and another for function calling in Python. For each diagram, call the tool "
        "`generate_mermaid_diagram` with arguments: outputType='svg', "
        "theme='default', backgroundColor='white'. Use ASCII identifiers in the "
        "diagrams (e.g., node_a, response_b). After each tool call, mention where "
        "the diagram is saved."
    )


if __name__ == "__main__":
    try:
        asyncio.run(run_mermaid_prompt(build_mermaid_prompt()))
    except Exception:
        logger.exception("Unhandled exception in main")
