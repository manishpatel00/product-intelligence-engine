"""
Zero-dependency Anthropic Claude client
=======================================
No ``pip install`` required — talks to the Claude Messages API over stdlib
``urllib`` so the whole engine runs on a bare Python install. Structured output
is obtained via a forced tool call (``tool_choice``), which is the reliable way
to make the model return schema-valid JSON instead of prose.

Config (env):
  ANTHROPIC_API_KEY   required to enable the AI path; if unset, callers fall
                      back to the deterministic pass and mark the row so.
  UNILOG_MODEL        model id (default: claude-sonnet-5).
  ANTHROPIC_BASE_URL  override endpoint (default https://api.anthropic.com).
"""

from __future__ import annotations
import json
import os
import time
import urllib.request
import urllib.error

DEFAULT_MODEL = os.environ.get("UNILOG_MODEL", "claude-sonnet-5")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.anthropic.com").rstrip("/")
API_VERSION = "2023-06-01"


class LLMUnavailable(RuntimeError):
    """Raised when no API key is configured (callers degrade gracefully)."""


def have_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def call_structured(system: str, user: str, tool_name: str, input_schema: dict,
                    model: str = None, max_tokens: int = 2048,
                    temperature: float = 0.0, max_retries: int = 4) -> dict:
    """Force Claude to return an object matching ``input_schema``.

    Returns the parsed tool-input dict. Raises LLMUnavailable if no key,
    or RuntimeError after exhausting retries.
    """
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise LLMUnavailable("ANTHROPIC_API_KEY not set")

    model = model or DEFAULT_MODEL
    body = {
        "model": model,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system,
        "messages": [{"role": "user", "content": user}],
        "tools": [{
            "name": tool_name,
            "description": "Emit the structured product record. "
                           "Every field MUST obey the rules in the system prompt.",
            "input_schema": input_schema,
        }],
        "tool_choice": {"type": "tool", "name": tool_name},
    }
    data = json.dumps(body).encode("utf-8")
    headers = {
        "content-type": "application/json",
        "x-api-key": key,
        "anthropic-version": API_VERSION,
    }

    last_err = None
    for attempt in range(max_retries):
        req = urllib.request.Request(f"{BASE_URL}/v1/messages", data=data,
                                     headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            for block in payload.get("content", []):
                if block.get("type") == "tool_use" and block.get("name") == tool_name:
                    return block["input"]
            raise RuntimeError(f"no tool_use block in response: {payload.get('content')}")
        except urllib.error.HTTPError as e:
            code = e.code
            last_err = f"HTTP {code}: {e.read().decode('utf-8', 'ignore')[:300]}"
            if code in (429, 500, 502, 503, 529):
                time.sleep(min(2 ** attempt, 20))
                continue
            raise RuntimeError(last_err)
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = f"network: {e}"
            time.sleep(min(2 ** attempt, 20))
    raise RuntimeError(f"LLM call failed after {max_retries} attempts: {last_err}")
