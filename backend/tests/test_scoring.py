from app.scoring import calculate_trend_score


def test_score_prioritizes_star_growth():
    score, stars_delta, forks_delta = calculate_trend_score(150, 20, 100, 18, "2026-06-29T00:00:00Z")
    assert stars_delta == 50
    assert forks_delta == 2
    assert score >= 506


def test_first_seen_repo_gets_baseline_but_no_delta():
    score, stars_delta, forks_delta = calculate_trend_score(1200, 40, None, None, None)
    assert stars_delta == 0
    assert forks_delta == 0
    assert score == 12
