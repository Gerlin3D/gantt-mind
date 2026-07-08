import json
from collections.abc import Mapping

from openai import APIError, OpenAI

from app.application.ai_contract import ALLOWED_AI_OPERATIONS
from app.application.exceptions import LlmProviderError

_SYSTEM_PROMPT = """You are a scheduling assistant for GanttMind, a project plan editor.

You translate a user's natural-language instruction into a strict JSON object that
describes structured changes to the given project plan. You do not calculate dates,
you do not invent task ids, and you never explain anything outside the JSON object.

Rules:
- Only use task ids that appear in the provided plan context. Never invent task ids.
- Only use these operation types: {allowed_operations}.
- If the instruction is ambiguous, unsafe, or cannot be mapped to the allowed
  operations using only the given task ids, return an empty "operations" list and
  put a short clarification or error message in "change_summary".
- Do not calculate or guess start_date/end_date values; the backend scheduler
  calculates dates.
- Respond with a single JSON object only, matching this shape and nothing else:
  {{"change_summary": "string", "operations": [ ... ]}}

Operation shapes:
- {{"type": "shift_tasks", "task_ids": ["id", ...], "offset_days": int}}
- {{"type": "change_duration", "task_id": "id", "duration_days": int}}
- {{"type": "change_assignee", "task_ids": ["id", ...], "assignee": "name or null"}}
- {{"type": "add_dependency", "predecessor_task_id": "id", "successor_task_id": "id"}}
- {{"type": "remove_dependency", "predecessor_task_id": "id", "successor_task_id": "id"}}

To move a task after another task, use "add_dependency" with the earlier task as
predecessor and the later task as successor.
""".format(allowed_operations=", ".join(ALLOWED_AI_OPERATIONS))


class OpenAILLMClient:
    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model

    def propose_operations(self, *, plan_context: Mapping[str, object], message: str) -> str:
        if not self._api_key:
            raise LlmProviderError("OPENAI_API_KEY is not configured on the backend.")

        user_content = json.dumps({"plan": plan_context, "instruction": message})
        client = OpenAI(api_key=self._api_key)

        try:
            response = client.chat.completions.create(
                model=self._model,
                temperature=0,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
        except APIError as error:
            raise LlmProviderError(f"The AI provider request failed: {error}") from error

        content = response.choices[0].message.content
        if not content:
            raise LlmProviderError("The AI provider returned an empty response.")
        return content
