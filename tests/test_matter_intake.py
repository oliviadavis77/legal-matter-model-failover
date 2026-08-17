from datetime import date

from legal_matter_failover.matter_intake import (
    IntakeAssessment,
    MatterIntake,
    build_matter_plan,
)


class FixedClassifier:
    def classify(self, matter: MatterIntake) -> IntakeAssessment:
        assert matter.matter_id == "MAT-204"
        return IntakeAssessment("employment", "high", "Counsel review requested.")


def test_signed_document_with_deadline_is_ready_and_scheduled() -> None:
    matter = MatterIntake(
        matter_id="MAT-204",
        client_name="Jordan Lee",
        summary="Response requested for an employment notice.",
        document_name="engagement-letter.pdf",
        document_signed=True,
        delivery_email="client@example.test",
        response_deadline=date(2026, 9, 4),
    )

    plan = build_matter_plan(matter, FixedClassifier())

    assert plan.delivery_status == "ready_for_signed_delivery"
    assert plan.follow_up_status == "deadline_follow_up_scheduled"
    assert plan.assessment.urgency == "high"


def test_unsigned_document_is_held_without_follow_up() -> None:
    matter = MatterIntake(
        matter_id="MAT-204",
        client_name="Jordan Lee",
        summary="Response requested for an employment notice.",
        document_name="engagement-letter.pdf",
        document_signed=False,
        delivery_email="client@example.test",
        response_deadline=date(2026, 9, 4),
    )

    plan = build_matter_plan(matter, FixedClassifier())

    assert plan.delivery_status == "hold_for_signature"
    assert plan.follow_up_status == "not_scheduled"
