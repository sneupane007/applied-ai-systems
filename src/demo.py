"""Run VibeMatch 2.0 end to end from the command line on three preset moments.

    python -m src.demo

Uses Claude when ANTHROPIC_API_KEY is set (in the environment or .env); otherwise runs offline.
Each run is also written to logs/vibematch.log under the run ID it prints.
"""
from src.context import GOALS, MOOD_CARDS, PLACES, Moment, time_of_day
from src.manual import load_manual
from src.retrieval import LocalCatalog
from src.vibe import Result, default_reasoner, recommend_for_moment, setup_logging

SCENARIOS = {
    "Rainy night at home": Moment(hour=23, mood_card="rainy_window", energy_level="Low", goal="match",
                                  place="home", weather="rainy", note="nothing too sad, just cozy"),
    "Storm at the gym": Moment(hour=18, mood_card="storm", energy_level="Wired", goal="energize", place="gym",
                               weather="sunny"),
    "Heart rate up on a cloudy afternoon": Moment(hour=15, mood_card="cozy_blanket", energy_level="Okay",
                                                  goal="match", place="home", weather="cloudy", heart_rate=110),
}


def describe(moment: Moment) -> str:
    parts = [MOOD_CARDS[moment.mood_card]["label"], f"energy {moment.energy_level}", GOALS[moment.goal],
             PLACES[moment.place], time_of_day(moment.hour), moment.weather or "weather unknown"]
    if moment.heart_rate is not None:
        parts.append(f"heart rate {moment.heart_rate} (simulated)")
    if moment.note:
        parts.append(f'note "{moment.note}"')
    return " · ".join(parts)


def show(name: str, moment: Moment, result: Result) -> None:
    t = result.target
    explanation = result.explanation
    print(f"=== {name} ===")
    print("moment: ", describe(moment))
    print("labels: ", ", ".join(result.labels))
    print("rules:  ", " · ".join(f"{r.id} {r.title}" for r in result.rules))
    print("nudges: ", " · ".join(result.nudges) or "none")
    print(f"target:  energy {t['energy']:.3f} · valence {t['valence']:.3f} · acoustic {t['acousticness']:.3f}")
    print(f"mode:    {explanation.mode} (run {result.run_id})")
    print()
    print(explanation.intro)
    for number, pick in enumerate(explanation.picks, start=1):
        s = pick.song
        rules = f" · rules {', '.join(pick.rule_ids)}" if pick.rule_ids else ""
        print(f"{number}. {s['title']} · {s['artist']} ({s['genre']}, energy {s['energy']:.2f}, "
              f"valence {s['valence']:.2f}, {s['tempo_bpm']:.0f} bpm{rules})")
        print(f"   {pick.reason}")
    if explanation.notes:
        print("check:  ", " ".join(explanation.notes))
    print()


def main() -> None:
    setup_logging()
    catalog, rules, reasoner = LocalCatalog(), load_manual(), default_reasoner()
    for name, moment in SCENARIOS.items():
        show(name, moment, recommend_for_moment(moment, catalog=catalog, reasoner=reasoner, rules=rules))


if __name__ == "__main__":
    main()
