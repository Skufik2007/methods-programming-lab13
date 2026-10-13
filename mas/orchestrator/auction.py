"""Чистая логика аукциона (раздел 6): выбор победителя и сбор ставок."""

from __future__ import annotations

import json
import logging
from datetime import datetime

from mas.common.models import Bid, parse_ts

log = logging.getLogger("mas.auction")


def bid_cost(skill: float, availability: float, load: float) -> float:
    """Формула контракта: 0.5·(1-availability) + 0.3·load + 0.2·(1-skill)."""
    return 0.5 * (1 - availability) + 0.3 * load + 0.2 * (1 - skill)


def _slot_key(slot_start: str) -> tuple[int, datetime | str]:
    try:
        return 0, parse_ts(slot_start)
    except ValueError:
        return 1, slot_start


def choose_winner(bids: list[Bid]) -> Bid | None:
    """Минимальный cost среди eligible; при равенстве — раньше slot_start, затем agent_id.

    Стоимость сравнивается с округлением до 9 знаков, чтобы шум float не ломал ничью.
    """
    eligible = [b for b in bids if b.eligible]
    if not eligible:
        return None
    return min(eligible, key=lambda b: (round(b.cost, 9), _slot_key(b.slot_start), b.agent_id))


def parse_bids(raw: list[bytes], auction_id: str) -> list[Bid]:
    """Разбирает ответы; битые и чужого аукциона пропускает, от одного агента берёт последнюю ставку."""
    by_agent: dict[str, Bid] = {}
    for item in raw:
        try:
            bid = Bid.model_validate(json.loads(item))
        except (ValueError, TypeError):
            log.warning("пропущена некорректная ставка")
            continue
        if bid.auction_id != auction_id:
            continue
        by_agent[bid.agent_id] = bid
    return list(by_agent.values())
