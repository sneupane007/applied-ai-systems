"""Load the music & mood manual and pick the rules that fit a moment.

The manual lives in knowledge/music_mood_manual.md; its header explains the format.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Set, Tuple

MANUAL_PATH = "knowledge/music_mood_manual.md"
MAX_MATCHED = 5  # rules picked per moment, on top of the always-on ones
MAX_NUDGE = 0.25
EVIDENCE_LEVELS = {"strong", "moderate", "limited", "design rule"}
REQUIRED_FIELDS = ("when", "nudge", "prefer", "avoid", "evidence", "why", "guidance", "sources")

# Manual wording -> song/target column names
AXES = {"energy": "energy", "valence": "valence", "acoustic": "acousticness"}
FEATURES = {
    "tempo": "tempo_bpm",
    "instrumental": "instrumentalness",
    "energy": "energy",
    "valence": "valence",
    "acoustic": "acousticness",
}


@dataclass
class Nudge:
    rule_id: str
    axis: str
    delta: float
    label: Optional[str] = None  # set when the nudge applies only with this label

    def describe(self) -> str:
        cause = f" {self.label}" if self.label else ""
        return f"{self.rule_id}{cause}: {self.axis} {self.delta:+.2f}"


@dataclass
class Rule:
    id: str
    title: str
    always: bool
    when: List[Set[str]]  # alternatives; each is a set of labels that must all be present
    nudges: List[Nudge]
    prefer: List[Tuple[str, float, float]]  # (song column, low, high)
    avoid: str
    evidence: str
    why: str
    guidance: str
    sources: str

    def score(self, labels: Set[str]) -> int:
        """How many labels the best-matching alternative uses (0 = no match)."""
        return max((len(alt) for alt in self.when if alt <= labels), default=0)


def _parse_changes(text: str, rule_id: str, label: Optional[str]) -> List[Nudge]:
    nudges = []
    for part in text.split(","):
        name, amount = part.split()
        if name not in AXES:
            raise ValueError(f"{rule_id}: unknown nudge axis '{name}'")
        delta = float(amount)
        if abs(delta) > MAX_NUDGE:
            raise ValueError(f"{rule_id}: nudge {delta} is larger than {MAX_NUDGE}")
        nudges.append(Nudge(rule_id, AXES[name], delta, label))
    return nudges


def _parse_nudges(text: str, rule_id: str) -> List[Nudge]:
    if text == "none":
        return []
    nudges = []
    for part in text.split("|"):
        part = part.strip()
        label = None
        if ":" in part:
            label, part = (s.strip() for s in part.split(":", 1))
        nudges += _parse_changes(part, rule_id, label)
    return nudges


def _parse_prefer(text: str, rule_id: str) -> List[Tuple[str, float, float]]:
    if text == "none":
        return []
    ranges = []
    for part in text.split(","):
        name, span = part.split()
        if name not in FEATURES:
            raise ValueError(f"{rule_id}: unknown preference '{name}'")
        low, high = (float(x) for x in span.split("-"))
        ranges.append((FEATURES[name], low, high))
    return ranges


def _parse_rule(heading: str, body: str) -> Rule:
    match = re.match(r"(M-\d+)\s*·\s*(.+)", heading)
    if not match:
        raise ValueError(f"Bad rule heading: '{heading}'")
    rule_id, title = match.group(1), match.group(2).strip()

    fields = {}
    for line in body.splitlines():
        line_match = re.match(r"-\s*(\w+):\s*(.*)", line.strip())
        if line_match:
            fields[line_match.group(1)] = line_match.group(2).strip()
    missing = [name for name in REQUIRED_FIELDS if not fields.get(name)]
    if missing:
        raise ValueError(f"{rule_id}: missing fields {missing}")
    if fields["evidence"] not in EVIDENCE_LEVELS:
        raise ValueError(f"{rule_id}: evidence must be one of {sorted(EVIDENCE_LEVELS)}")

    always = fields["when"] == "always"
    when = [] if always else [
        {label.strip() for label in alt.split("+")} for alt in fields["when"].split(",")
    ]
    return Rule(
        id=rule_id,
        title=title,
        always=always,
        when=when,
        nudges=_parse_nudges(fields["nudge"], rule_id),
        prefer=_parse_prefer(fields["prefer"], rule_id),
        avoid=fields["avoid"],
        evidence=fields["evidence"],
        why=fields["why"],
        guidance=fields["guidance"],
        sources=fields["sources"],
    )


def load_manual(path: str = MANUAL_PATH) -> List[Rule]:
    """Parse every '## M-XX · Title' section of the manual into a Rule."""
    with open(path, encoding="utf-8") as f:
        text = f.read()
    sections = re.split(r"^## (?=M-\d+)", text, flags=re.MULTILINE)[1:]
    rules = []
    for section in sections:
        heading, _, body = section.partition("\n")
        rules.append(_parse_rule(heading.strip(), body))
    ids = [rule.id for rule in rules]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate rule IDs in the manual")
    return rules


def match_rules(rules: List[Rule], labels: List[str], max_matched: int = MAX_MATCHED) -> List[Rule]:
    """Always-on rules plus the best-matching ones, in manual order."""
    label_set = set(labels)
    scored = [(rule.score(label_set), i, rule) for i, rule in enumerate(rules) if not rule.always]
    best = sorted((s for s in scored if s[0] > 0), key=lambda s: (-s[0], s[1]))[:max_matched]
    chosen = {rule.id for _, _, rule in best}
    return [rule for rule in rules if rule.always or rule.id in chosen]


def nudges_for(rules: List[Rule], labels: List[str]) -> List[Nudge]:
    """The nudges of the given rules that apply to these labels."""
    label_set = set(labels)
    return [n for rule in rules for n in rule.nudges if n.label is None or n.label in label_set]


def preferences_for(rules: List[Rule]) -> List[Tuple[str, float, float]]:
    return [pref for rule in rules for pref in rule.prefer]


def prompt_text(rules: List[Rule]) -> str:
    """The rules as the AI reads them."""
    blocks = []
    for rule in rules:
        blocks.append(
            f"[{rule.id}] {rule.title} (evidence: {rule.evidence})\n"
            f"Guidance: {rule.guidance}\n"
            f"Avoid: {rule.avoid}"
        )
    return "\n\n".join(blocks)
