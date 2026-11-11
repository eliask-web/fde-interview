"""The only place a Claude client is built. Routed through Portkey."""

import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic


def get_llm(fast: bool = False) -> ChatAnthropic:
    load_dotenv()
    if fast:
        model = os.getenv("ANTHROPIC_FAST_MODEL", "claude-haiku-5-5")
    else:
        model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5-5")
    return ChatAnthropic(
        model=model,
        base_url="https://api.portkey.ai",
        api_key="portkey-routed",  # placeholder; Portkey holds the real key
        default_headers={
            "x-portkey-api-key": os.getenv("PORTKEY_API_KEY", ""),
            "x-portkey-virtual-key": os.getenv("PORTKEY_VIRTUAL_KEY", ""),
        },
        max_tokens=2048,
    )
