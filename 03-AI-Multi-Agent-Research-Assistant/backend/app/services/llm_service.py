import json
from typing import TypeVar
from groq import Groq
from pydantic import BaseModel, ValidationError
from app.config import get_settings

T = TypeVar("T", bound=BaseModel)

class LLMService:
    def __init__(self) -> None:
        settings = get_settings()
        self.client = Groq(api_key=settings.groq_api_key)
        self.model = settings.groq_model

    def structured(self, system: str, prompt: str, schema: type[T]) -> T:
        result = self.client.chat.completions.create(model=self.model, messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}], response_format={"type": "json_object"}, temperature=0.2)
        content = result.choices[0].message.content
        if not content:
            raise RuntimeError("Groq returned an empty response")
        try:
            return schema.model_validate(json.loads(content))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise RuntimeError(f"Groq returned invalid structured output for {schema.__name__}") from exc
