from db import players, Player
import time

def track_quest_progress(user_id, action_type, amount=1, extra=None):
    p_list = players.search(Player.id == user_id)
    if not p_list:
        return []
    p = p_list[0]
    active_quests = p.get('active_quests', [])
    if not active_quests:
        return []

    completed_ids = []
    updated = False

    for quest in active_quests:
        if quest.get('progress', 0) >= quest.get('required', 1):
            continue
        obj = quest.get('objective_type', '')
        matched = False

        if obj == action_type:
            matched = True
        elif obj.startswith('arc_win_') and action_type == 'arc_win':
            req_arc = obj.replace('arc_win_', '')
            if extra is not None and str(extra) == req_arc:
                matched = True
        elif obj.startswith('raid_defeat') and action_type == 'raid_defeat':
            matched = True

        if matched:
            quest['progress'] = min(quest.get('progress', 0) + amount, quest.get('required', 1))
            updated = True
            if quest['progress'] >= quest['required']:
                completed_ids.append(quest['quest_id'])

    if updated:
        players.update({'active_quests': active_quests}, Player.id == user_id)

    return completed_ids
