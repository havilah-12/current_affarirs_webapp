"""Reading-activity / daily-streak endpoints.

Tracks one row per (user, calendar day) every time the user opens the news
feed. Drives the gamification widgets on the dashboard:

- `POST /activity/ping`  : idempotently mark "the user opened news today".
- `GET  /activity/stats` : current streak, longest streak, this-month count,
                           total days, and a 30-day heatmap.

Days are computed in UTC. For a single-user-per-day-streak feature this is
fine; if/when we want timezone-personalised streaks the UTC date can be
swapped for a user-supplied IANA tz on the request.
"""

from __future__ import annotations

from calendar import monthrange
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, Query
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..deps import get_current_user, get_db
from ..models import ReadingActivity, User
from ..schemas import ActivityPingIn, ActivityPingResponse, ActivityStats, ReadDayInMonth


router = APIRouter(prefix="/activity", tags=["activity"])


def _today_utc() -> date:
    """Return the current UTC calendar day."""
    return datetime.now(timezone.utc).date()


def _user_days(db: Session, user_id: int) -> List[date]:
    """Return all distinct days the user has opened the news, ascending."""
    rows = db.execute(
        select(ReadingActivity.day)
        .where(ReadingActivity.user_id == user_id)
        .order_by(ReadingActivity.day.asc())
    ).all()
    return [row[0] for row in rows]


def _compute_streaks(days: List[date], today: date) -> tuple[int, int]:
    """Return (current_streak, longest_streak) for an ASC-sorted unique day list.

    A "current streak" is the unbroken run ending at either today or yesterday
    (yesterday lets the user keep the streak alive until they open the app).
    """
    if not days:
        return 0, 0

    # Longest run anywhere in history.
    longest = 1
    run = 1
    for prev, curr in zip(days, days[1:]):
        if (curr - prev).days == 1:
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    # Current streak ending at today/yesterday.
    last = days[-1]
    if last < today - timedelta(days=1):
        current = 0
    else:
        current = 1
        # walk backwards from `last` while consecutive
        for prev, curr in zip(reversed(days[:-1]), reversed(days[1:])):
            if (curr - prev).days == 1:
                current += 1
            else:
                break
    return current, longest


@router.post(
    "/ping",
    response_model=ActivityPingResponse,
    summary="Record that the current user opened the news today",
)
def ping_activity(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    body: Optional[ActivityPingIn] = Body(default=None),
) -> ActivityPingResponse:
    """Insert a (user, today) row if absent. Idempotent within a UTC day.

    Optional `category` stores the last news filter category for that UTC day
    (updated on repeat pings the same day).
    """
    today = _today_utc()
    payload = body or ActivityPingIn()

    row = (
        db.execute(
            select(ReadingActivity).where(
                ReadingActivity.user_id == user.id,
                ReadingActivity.day == today,
            )
        )
        .scalars()
        .one_or_none()
    )

    recorded = False
    if row is None:
        db.add(ReadingActivity(user_id=user.id, day=today, category=payload.category))
        try:
            db.commit()
            recorded = True
        except IntegrityError:
            db.rollback()
            row = (
                db.execute(
                    select(ReadingActivity).where(
                        ReadingActivity.user_id == user.id,
                        ReadingActivity.day == today,
                    )
                )
                .scalars()
                .one_or_none()
            )
    if row is not None and payload.category is not None and row.category != payload.category:
        row.category = payload.category
        db.commit()

    days = _user_days(db, user.id)
    current, longest = _compute_streaks(days, today)
    return ActivityPingResponse(
        today=today,
        recorded=recorded,
        current_streak=current,
        longest_streak=longest,
    )


@router.get(
    "/stats",
    response_model=ActivityStats,
    summary="Return daily-streak stats + 30-day heatmap for the dashboard",
)
def get_activity_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    cal_year: int | None = Query(
        default=None,
        description="Calendar year (UTC) for `read_days_in_month`. Defaults to this month.",
    ),
    cal_month: int | None = Query(
        default=None,
        ge=1,
        le=12,
        description="1-12 (UTC) for `read_days_in_month`. Defaults to this month.",
    ),
) -> ActivityStats:
    today = _today_utc()
    days = _user_days(db, user.id)
    days_set = set(days)

    current, longest = _compute_streaks(days, today)

    month_start = today.replace(day=1)
    days_this_month = sum(1 for d in days_set if d >= month_start)

    window_start = today - timedelta(days=29)  # 30-day window incl. today
    last_30 = sorted(d for d in days_set if d >= window_start)

    y = cal_year if cal_year is not None else today.year
    m = cal_month if cal_month is not None else today.month
    m_start = date(y, m, 1)
    m_end = date(y, m, monthrange(y, m)[1])

    read_rows = db.execute(
        select(ReadingActivity.day, ReadingActivity.category)
        .where(ReadingActivity.user_id == user.id)
        .where(ReadingActivity.day >= m_start, ReadingActivity.day <= m_end)
        .order_by(ReadingActivity.day.asc())
    ).all()
    read_days_in_month = [ReadDayInMonth(day=row[0], category=row[1]) for row in read_rows]

    return ActivityStats(
        today=today,
        read_today=today in days_set,
        current_streak=current,
        longest_streak=longest,
        days_this_month=days_this_month,
        total_days=len(days_set),
        last_30_days=last_30,
        calendar_year=y,
        calendar_month=m,
        read_days_in_month=read_days_in_month,
    )
