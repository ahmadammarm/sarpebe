"""Evaluation examples: a topic a teacher might type, and where in the documents the answer lives."""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DEFAULT_DATASET = Path(__file__).parent / "data" / "retrieval_set.jsonl"


@dataclass(frozen=True)
class Example:
    topic: str
    grade_level: str
    subject: str
    # "positive": the documents cover this topic; `gold` lists where (document_id, page).
    # "negative": the documents do NOT cover it; the right behavior is to find nothing relevant.
    kind: Literal["positive", "negative"]
    gold: tuple[tuple[str, int], ...] = ()

    def to_json(self) -> str:
        return json.dumps(
            {
                "topic": self.topic,
                "grade_level": self.grade_level,
                "subject": self.subject,
                "kind": self.kind,
                "gold": [list(item) for item in self.gold],
            },
            ensure_ascii=False,
        )

    @staticmethod
    def from_json(line: str) -> "Example":
        data = json.loads(line)
        return Example(
            topic=data["topic"],
            grade_level=data["grade_level"],
            subject=data["subject"],
            kind=data["kind"],
            gold=tuple((str(doc), int(page)) for doc, page in data.get("gold", [])),
        )


def load_examples(path: Path = DEFAULT_DATASET) -> list[Example]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} does not exist. Create it with: python -m evals.run questions"
        )
    return [Example.from_json(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def save_examples(examples: list[Example], path: Path = DEFAULT_DATASET) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(example.to_json() for example in examples) + "\n", encoding="utf-8")
