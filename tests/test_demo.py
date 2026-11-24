from src import demo


def test_demo_runs_every_scenario_end_to_end_offline(monkeypatch, capsys):
    monkeypatch.setattr(demo, "default_reasoner", lambda: None)
    monkeypatch.setattr(demo, "setup_logging", lambda: None)
    demo.main()
    out = capsys.readouterr().out
    for name in demo.SCENARIOS:
        assert f"=== {name} ===" in out
    assert out.count("mode:    offline") == len(demo.SCENARIOS)
    assert out.count("\n5. ") == len(demo.SCENARIOS)
