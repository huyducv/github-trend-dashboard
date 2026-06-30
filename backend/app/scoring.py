from datetime import datetime, timezone


def calculate_trend_score(
    stars: int,
    forks: int,
    previous_stars: int | None,
    previous_forks: int | None,
    pushed_at: str | None,
) -> tuple[float, int, int]:
    stars_delta = max(0, stars - previous_stars) if previous_stars is not None else 0
    forks_delta = max(0, forks - previous_forks) if previous_forks is not None else 0
    recency_bonus = _recency_bonus(pushed_at)

    score = (stars_delta * 10) + (forks_delta * 3) + recency_bonus
    if previous_stars is None:
        score += min(stars, 5000) / 100
    return round(score, 2), stars_delta, forks_delta


def _recency_bonus(pushed_at: str | None) -> float:
    if not pushed_at:
        return 0
    try:
        pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
    except ValueError:
        return 0
    age_days = max(0, (datetime.now(timezone.utc) - pushed).days)
    if age_days <= 1:
        return 8
    if age_days <= 7:
        return 4
    if age_days <= 30:
        return 1
    return 0
