from typing import Optional

import requests

from .config import settings


class AIHubClient:
    def __init__(self) -> None:
        self.base_url = settings.ai_hub_base_url
        self.api_key = settings.ai_hub_api_key
        self.model = settings.ai_hub_model
        self.timeout = settings.ai_hub_timeout_seconds

    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key)

    def generate(self, prompt: str) -> Optional[str]:
        if not self.enabled():
            return None

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a clinical summarization assistant focused on pandemic respiratory risk and continuity of care.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        response.raise_for_status()

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            return None
        return choices[0].get("message", {}).get("content")
