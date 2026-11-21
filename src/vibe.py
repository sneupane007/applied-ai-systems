"""VibeMatch 2.0 pipeline:
moment -> labels -> manual rules -> target point -> nearest songs -> AI picks -> grounding check.

Every run is logged to logs/vibematch.log under a run ID. Raw signals, the city, and the
note text are never logged.
"""
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv

from src.context import Moment, apply_nudges, base_point, labels_for, time_of_day, validate
from src.explainer import ClaudeReasoner, Explanation, Reasoner, explain
from src.manual import Rule, load_manual, match_rules, nudges_for, preferences_for
from src.privacy import for_reasoner, music_intent
from src.retrieval import LocalCatalog, MusicSource

LOG_PATH = "logs/vibematch.log"
logger = logging.getLogger("vibematch")

CRISIS_WORDS = (
    "suicide", "suicidal", "kill myself", "end my life", "want to die", "self harm",
    "self-harm", "hurt myself", "don't want to live", "dont want to live", "no reason to live",
)
SUPPORT_MESSAGE = (
    "It sounds like things might be really hard right now. You don't have to handle it alone. "
    "In the US, you can call or text 988 (Suicide & Crisis Lifeline) any time. "
    "Elsewhere, findahelpline.com lists free local helplines. If you're in immediate danger, "
    "call your local emergency number."
)


@dataclass
class Result:
    run_id: str
    labels: List[str]
    rules: List[Rule]
    nudges: List[str]
    base: Dict[str, float]
    target: Dict[str, float]
    candidates: List[Tuple[Dict, float]]
    explanation: Explanation
    support_message: Optional[str] = None


def setup_logging(path: str = LOG_PATH) -> None:
    """Send the 'vibematch' logger to a file (once per process)."""
    if logger.handlers:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def default_reasoner() -> Optional[Reasoner]:
    """Claude when ANTHROPIC_API_KEY is set (from the environment or .env); otherwise offline."""
    load_dotenv()
    return ClaudeReasoner() if os.getenv("ANTHROPIC_API_KEY") else None


def needs_support(note: str) -> bool:
    text = note.lower()
    return any(word in text for word in CRISIS_WORDS)


def recommend_for_moment(moment: Moment, catalog: Optional[MusicSource] = None,
                         reasoner: Optional[Reasoner] = None, rules: Optional[List[Rule]] = None) -> Result:
    run_id = uuid.uuid4().hex[:8]
    validate(moment)

    labels = labels_for(moment)
    logger.info("run=%s inputs card=%s energy=%s goal=%s place=%s time=%s weather=%s note_chars=%d",
                run_id, moment.mood_card, moment.energy_level, moment.goal, moment.place,
                time_of_day(moment.hour), moment.weather or "unknown", len(moment.note))
    logger.info("run=%s labels=%s", run_id, labels)

    matched = match_rules(rules if rules is not None else load_manual(), labels)
    nudges = nudges_for(matched, labels)
    base = base_point(moment)
    target = apply_nudges(base, nudges)
    logger.info("run=%s rules=%s nudges=%s base=%s target=%s", run_id, [r.id for r in matched],
                [n.describe() for n in nudges], base, target)

    intent = music_intent(target, preferences_for(matched))
    candidates = (catalog or LocalCatalog()).search(intent)
    logger.info("run=%s retrieved=%s", run_id, [(s["id"], d) for s, d in candidates])

    support = SUPPORT_MESSAGE if needs_support(moment.note) else None
    if support:
        # Don't send a note like this anywhere: use offline picks and show support first.
        logger.warning("run=%s support message shown; note not sent to the AI", run_id)
        reasoner = None

    started = time.monotonic()
    explanation = explain(reasoner, for_reasoner(moment, labels), matched, candidates, labels, moment.goal, target)
    latency_ms = round((time.monotonic() - started) * 1000)
    logger.info("run=%s mode=%s latency_ms=%d request_id=%s picks=%s", run_id, explanation.mode, latency_ms,
                getattr(reasoner, "last_request_id", None),
                [(p.song["id"], p.rule_ids) for p in explanation.picks])
    if explanation.rejected_song_ids or explanation.rejected_rule_ids:
        logger.warning("run=%s rejected songs=%s rules=%s", run_id,
                       explanation.rejected_song_ids, explanation.rejected_rule_ids)
    for note in explanation.notes:
        logger.info("run=%s check: %s", run_id, note)

    return Result(run_id, labels, matched, [n.describe() for n in nudges], base, target,
                  candidates, explanation, support)
