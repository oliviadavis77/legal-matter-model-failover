"""Executable matter-intake example."""

import argparse
import json
from pathlib import Path

from legal_matter_failover.matter_intake import (
    InfraiIntakeClassifier,
    MatterIntake,
    build_matter_plan,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a legal matter delivery plan")
    parser.add_argument("request", type=Path, help="path to a matter intake JSON file")
    args = parser.parse_args()
    matter = MatterIntake.model_validate_json(args.request.read_text(encoding="utf-8"))
    plan = build_matter_plan(matter, InfraiIntakeClassifier())
    print(json.dumps(plan.to_dict(), indent=2))


if __name__ == "__main__":
    main()
