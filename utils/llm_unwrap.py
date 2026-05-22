"""Strip JSON envelopes that LLMs sometimes wrap chat replies in.

Mistral on Bedrock (and a few others) occasionally returns chat replies
shaped like `{"message": "Hello!"}` or `{"answer": "..."}` because the
tool-calling system prompts we use elsewhere train them on that JSON
contract. The chitchat / synthesizer paths shouldn't show that wire
format to the user — strip it before it lands in the conversation.

Conservative on purpose: if the text isn't unambiguously a JSON
envelope, return it untouched. Better to leak a rare envelope than to
mangle a legitimate code-block reply.
"""
from __future__ import annotations

import json
import re

# Keys we consider "the actual reply" inside a JSON envelope. Order
# matters — earlier keys win when more than one is present.
_REPLY_KEYS = ("answer", "message", "text", "reply", "response", "content")

_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL)


def unwrap_llm_reply(raw: str) -> str:
    """Return `raw` with any outer JSON envelope removed.

    Handles:
      - {"message": "Hello!"}            -> Hello!
      - {"answer": ["a", "b"]}           -> a\n- b
      - ```json\n{"answer": "..."}\n```  -> ...
      - plain text                       -> unchanged
    """
    if not isinstance(raw, str):
        return raw
    s = raw.strip()
    if not s:
        return s

    # Peel a single markdown code fence if the whole thing is wrapped in
    # one. We don't peel fences that are clearly part of a longer reply.
    m = _FENCE_RE.match(s)
    if m:
        s = m.group(1).strip()

    # Must look like a JSON object before we attempt to parse — avoid
    # touching anything else.
    if not (s.startswith("{") and s.endswith("}")):
        return raw

    try:
        obj = json.loads(s)
    except (json.JSONDecodeError, ValueError):
        return raw

    if not isinstance(obj, dict):
        return raw

    # Find the first reply-shaped key with a usable value.
    for k in _REPLY_KEYS:
        if k not in obj:
            continue
        val = obj[k]
        if isinstance(val, str) and val.strip():
            return val.strip()
        if isinstance(val, list) and val:
            # Render lists as bullet lines — matches how Bedrock's
            # envelope sometimes returns multi-point answers.
            lines = [str(x).strip() for x in val if str(x).strip()]
            if lines:
                return "\n".join(f"- {line}" for line in lines)

    # Envelope-shaped but no recognizable reply field — return the
    # original so we don't accidentally hide the model's output.
    return raw
