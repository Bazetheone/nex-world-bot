# Stat system helpers: percentage gear, Magic Power, effective stats.
# Nothing here writes to the database.

STAT_KEYS = ('hp', 'str', 'def', 'mag')
MAIN_THRESHOLD = 0.8
UPGRADE_STEP = 0.3

# rarity: (main stat %, other stat %)
GEAR_PCT = {
    'Common': (1.0, 0.5), 'Uncommon': (2.0, 1.0), 'Rare': (3.0, 1.5),
    'Epic': (5.0, 2.5), 'Legendary': (8.0, 4.0), 'Mythic': (12.0, 6.0),
    'Mythical': (12.0, 6.0), 'Divine': (14.0, 7.0), 'Celestial': (15.0, 7.5),
    'Godly': (16.0, 8.0),
}

# rarity: main stat % (other stats get half)
PET_PCT = {
    'Common': 2.0, 'Uncommon': 3.0, 'Rare': 4.0, 'Epic': 6.0,
    'Legendary': 8.0, 'Mythic': 11.0, 'Mythical': 11.0, 'Divine': 15.0,
    'Celestial': 15.0, 'Godly': 15.0,
}


def derive_item_pct(item, is_pet=False):
    existing = item.get('pct')
    if existing:
        return {k: float(v) for k, v in existing.items() if k in STAT_KEYS}
    stats = {k: v for k, v in (item.get('stats') or {}).items() if k in STAT_KEYS and v}
    if not stats:
        return {}
    rarity = item.get('rarity', 'Common')
    if is_pet or item.get('type') == 'pet':
        main = PET_PCT.get(rarity, PET_PCT['Common'])
        other = main / 2
    else:
        main, other = GEAR_PCT.get(rarity, GEAR_PCT['Common'])
    top = max(stats.values())
    return {k: (main if v >= top * MAIN_THRESHOLD else other) for k, v in stats.items()}


def _affinity(item_name, race):
    try:
        from cogs.shop import get_affinity_multiplier
        return get_affinity_multiplier(item_name, race)
    except Exception:
        return 1.0


def get_gear_bonuses(p):
    bonus = {k: 0.0 for k in STAT_KEYS}
    race = p.get('race')
    for slot, item in (p.get('equipped') or {}).items():
        if not item or not isinstance(item, dict):
            continue
        pct = derive_item_pct(item, is_pet=(slot == 'pet'))
        mult = _affinity(item.get('name', ''), race)
        up = 1 + UPGRADE_STEP * (item.get('upgrade_level', 1) - 1)
        for stat, val in pct.items():
            bonus[stat] += val * mult * up
    return bonus


def old_flat_bonus(p):
    total = {k: 0 for k in STAT_KEYS}
    for slot, item in (p.get('equipped') or {}).items():
        if item and isinstance(item, dict):
            for stat, val in (item.get('stats') or {}).items():
                if stat in total:
                    total[stat] += val
    return total


def base_stats(p):
    base = {k: p.get(k, 0) for k in STAT_KEYS}
    if p.get('stats_version', 1) < 2:
        flat = old_flat_bonus(p)
        for k in STAT_KEYS:
            base[k] = max(1, base[k] - flat[k])
    return base


def get_effective_stats(p):
    base = base_stats(p)
    bonus = get_gear_bonuses(p)
    eff = {k: int(base[k] * (1 + bonus[k] / 100)) for k in ('hp', 'str', 'def')}
    mp_pct = min(100.0, base['mag'] / 100 + bonus['mag'])
    eff['magic_power_pct'] = mp_pct
    eff['magic_power'] = mp_pct / 100
    return eff, base, bonus


def magic_bar(pct, length=10):
    filled = int(round(pct / 100 * length))
    filled = max(0, min(length, filled))
    return "▰" * filled + "▱" * (length - filled) + f" {pct:.1f}%"
