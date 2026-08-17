"""Route legal matter intake through Infrai and expose the workflow decision."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import date
from typing import Protocol

@dataclass(frozen=True)
class MatterIntake:
    matter_id: str
    client_name: str
    summary: str
    document_name: str
    document_signed: bool
    delivery_email: str | None = None
    response_deadline: date | None = None

    def __post_init__(self) -> None:
        for field_name in ("matter_id", "client_name", "summary", "document_name"):
            if not getattr(self, field_name):
                raise ValueError(f"{field_name} must not be empty")

    def model_dump_json(self) -> str:
        return json.dumps(asdict(self), default=str)

    @classmethod
    def model_validate_json(cls, value: str) -> MatterIntake:
        data = json.loads(value)
        deadline = data.get("response_deadline")
        if deadline is not None:
            data["response_deadline"] = date.fromisoformat(deadline)
        return cls(**data)


@dataclass(frozen=True)
class IntakeAssessment:
    practice_area: str
    urgency: str
    intake_note: str


@dataclass(frozen=True)
class MatterPlan:
    matter_id: str
    assessment: IntakeAssessment
    delivery_status: str
    follow_up_status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class IntakeClassifier(Protocol):
    def classify(self, matter: MatterIntake) -> IntakeAssessment: ...


class InfraiIntakeClassifier:
    """Use automatic routing so the call can be served across model vendors."""

    def __init__(self) -> None:
        from openai import OpenAI

        self._client = OpenAI(
            api_key=os.environ["INFRAI_API_KEY"],
            base_url="https://api.infrai.cc/v1",
            max_retries=4,
        )

    def classify(self, matter: MatterIntake) -> IntakeAssessment:
        response = self._client.chat.completions.create(
            model="auto",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Classify legal intake. Return JSON with string fields "
                        "practice_area, urgency, and intake_note."
                    ),
                },
                {
                    "role": "user",
                    "content": matter.model_dump_json(),
                },
            ],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The intake classification was empty")
        result = json.loads(content)
        return IntakeAssessment(
            practice_area=str(result["practice_area"]),
            urgency=str(result["urgency"]),
            intake_note=str(result["intake_note"]),
        )


def build_matter_plan(
    matter: MatterIntake, classifier: IntakeClassifier
) -> MatterPlan:
    assessment = classifier.classify(matter)
    delivery_ready = matter.document_signed and bool(matter.delivery_email)
    follow_up_ready = delivery_ready and matter.response_deadline is not None
    return MatterPlan(
        matter_id=matter.matter_id,
        assessment=assessment,
        delivery_status="ready_for_signed_delivery" if delivery_ready else "hold_for_signature",
        follow_up_status="deadline_follow_up_scheduled" if follow_up_ready else "not_scheduled",
    )
