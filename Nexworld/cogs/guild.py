import discord
from discord.ext import commands
from tinydb import TinyDB, Query
from db import players, Player
import random
import time
import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from quest_tracker import track_quest_progress

GOLD = 0xFFD700

RANKS = {
    "F": {"rep_req": 0,     "max_active": 3, "max_daily": 2, "max_weekly": 5,  "rep_loss": 10},
    "E": {"rep_req": 500,   "max_active": 3, "max_daily": 3, "max_weekly": 7,  "rep_loss": 25},
    "D": {"rep_req": 1500,  "max_active": 3, "max_daily": 4, "max_weekly": 9,  "rep_loss": 60},
    "C": {"rep_req": 4000,  "max_active": 3, "max_daily": 5, "max_weekly": 11, "rep_loss": 120},
    "B": {"rep_req": 10000, "max_active": 3, "max_daily": 6, "max_weekly": 13, "rep_loss": 250},
    "A": {"rep_req": 25000, "max_active": 3, "max_daily": 7, "max_weekly": 15, "rep_loss": 500},
    "S": {"rep_req": 60000, "max_active": 3, "max_daily": 8, "max_weekly": 20, "rep_loss": 1000},
}
RANK_ORDER = ["F", "E", "D", "C", "B", "A", "S"]
RANK_ICONS = {"F": "🩶", "E": "🤍", "D": "🩵", "C": "💚", "B": "💛", "A": "🧡", "S": "❤️"}

QUESTS = {
    "F": [
        {"id":"FQ-001","title":"First Steps","desc":"Use `!explore` 3 times","obj":"explore","req":3,"time_h":12,"type":"Daily","rep":15,"nc":50,"cc":5},
        {"id":"FQ-002","title":"Herb Beginner","desc":"Use `!gather` to collect 5 medicinal herbs","obj":"gather","req":5,"time_h":24,"type":"Daily","rep":20,"nc":80,"cc":8},
        {"id":"FQ-003","title":"Message Runner","desc":"Complete a `!travel` mission","obj":"travel","req":1,"time_h":8,"type":"Daily","rep":25,"nc":100,"cc":10},
        {"id":"FQ-004","title":"Hourly Diligence","desc":"Use `!hourly` 3 times","obj":"hourly","req":3,"time_h":24,"type":"Daily","rep":15,"nc":60,"cc":6},
        {"id":"FQ-005","title":"Sparring Basics","desc":"Use `!fight` on another player","obj":"fight","req":1,"time_h":12,"type":"Daily","rep":20,"nc":75,"cc":7},
        {"id":"FQ-006","title":"Consistent Worker","desc":"Use `!hourly` 5 times","obj":"hourly","req":5,"time_h":72,"type":"Weekly","rep":80,"nc":300,"cc":30},
        {"id":"FQ-007","title":"Weekend Wanderer","desc":"Use `!explore` 10 times","obj":"explore","req":10,"time_h":72,"type":"Weekly","rep":90,"nc":350,"cc":35},
        {"id":"FQ-008","title":"Novice Herbalist","desc":"Gather 15 medicinal herbs","obj":"gather","req":15,"time_h":120,"type":"Weekly","rep":120,"nc":500,"cc":50},
        {"id":"FQ-009","title":"Road to Somewhere","desc":"Complete 3 `!travel` missions","obj":"travel","req":3,"time_h":96,"type":"Weekly","rep":100,"nc":400,"cc":40},
        {"id":"FQ-010","title":"First Bout","desc":"Win a `!fight` against another player","obj":"fight_win","req":1,"time_h":24,"type":"Daily","rep":30,"nc":120,"cc":12},
        {"id":"FQ-011","title":"Rock Bottom","desc":"Complete a `!travel` mission","obj":"travel","req":1,"time_h":12,"type":"Daily","rep":35,"nc":140,"cc":14},
        {"id":"FQ-012","title":"Guild Card","desc":"Check `!guild board` for the first time","obj":"guild_board","req":1,"time_h":6,"type":"Daily","rep":10,"nc":30,"cc":3},
        {"id":"FQ-013","title":"Listening Ear","desc":"Use `!hourly` once","obj":"hourly","req":1,"time_h":6,"type":"Daily","rep":10,"nc":30,"cc":3},
        {"id":"FQ-014","title":"Small Mercies","desc":"Complete a `!gather` run","obj":"gather","req":3,"time_h":24,"type":"Daily","rep":20,"nc":70,"cc":7},
        {"id":"FQ-015","title":"Dirt Roads","desc":"Use `!explore` twice","obj":"explore","req":2,"time_h":24,"type":"Daily","rep":25,"nc":90,"cc":9},
        {"id":"FQ-016","title":"Carry the Load","desc":"Complete 5 `!travel` missions","obj":"travel","req":5,"time_h":120,"type":"Weekly","rep":110,"nc":450,"cc":45},
        {"id":"FQ-017","title":"Steady Hands","desc":"Use `!gather` 10 times","obj":"gather","req":10,"time_h":96,"type":"Weekly","rep":130,"nc":520,"cc":52},
        {"id":"FQ-018","title":"Scrapper","desc":"Win 3 `!fight` duels","obj":"fight_win","req":3,"time_h":120,"type":"Weekly","rep":140,"nc":560,"cc":56},
        {"id":"FQ-019","title":"Keeping Pace","desc":"Use `!hourly` 10 times","obj":"hourly","req":10,"time_h":168,"type":"Weekly","rep":150,"nc":600,"cc":60},
        {"id":"FQ-020","title":"Iron Will","desc":"Win 2 `!fight` duels","obj":"fight_win","req":2,"time_h":72,"type":"Weekly","rep":160,"nc":640,"cc":64},
    ],
    "E": [
        {"id":"EQ-001","title":"Wilderness Walk","desc":"Use `!explore` 8 times","obj":"explore","req":8,"time_h":24,"type":"Daily","rep":40,"nc":160,"cc":16},
        {"id":"EQ-002","title":"Field Medic Supplies","desc":"Gather 10 medicinal herbs","obj":"gather","req":10,"time_h":24,"type":"Daily","rep":45,"nc":180,"cc":18},
        {"id":"EQ-003","title":"Courier's Trial","desc":"Complete 2 `!travel` missions","obj":"travel","req":2,"time_h":24,"type":"Daily","rep":50,"nc":200,"cc":20},
        {"id":"EQ-004","title":"Clock Puncher","desc":"Use `!hourly` 5 times","obj":"hourly","req":5,"time_h":24,"type":"Daily","rep":35,"nc":150,"cc":15},
        {"id":"EQ-005","title":"Blood and Bruises","desc":"Win 2 `!fight` duels","obj":"fight_win","req":2,"time_h":24,"type":"Daily","rep":55,"nc":220,"cc":22},
        {"id":"EQ-006","title":"Seeking Strength","desc":"Use `!explore` 20 times","obj":"explore","req":20,"time_h":96,"type":"Weekly","rep":200,"nc":800,"cc":80},
        {"id":"EQ-007","title":"Herbalist's Week","desc":"Gather 40 medicinal herbs","obj":"gather","req":40,"time_h":168,"type":"Weekly","rep":240,"nc":960,"cc":96},
        {"id":"EQ-008","title":"Road Veteran","desc":"Complete 8 `!travel` missions","obj":"travel","req":8,"time_h":168,"type":"Weekly","rep":220,"nc":880,"cc":88},
        {"id":"EQ-009","title":"Duel Record","desc":"Win 5 `!fight` duels","obj":"fight_win","req":5,"time_h":120,"type":"Weekly","rep":260,"nc":1040,"cc":104},
        {"id":"EQ-010","title":"Disciplined","desc":"Use `!hourly` 12 times","obj":"hourly","req":12,"time_h":168,"type":"Weekly","rep":210,"nc":840,"cc":84},
        {"id":"EQ-011","title":"Lone Wolf","desc":"Win a `!fight` duel","obj":"fight_win","req":1,"time_h":24,"type":"Daily","rep":60,"nc":240,"cc":24},
        {"id":"EQ-012","title":"Herb Rush","desc":"Gather 5 herbs","obj":"gather","req":5,"time_h":24,"type":"Daily","rep":65,"nc":260,"cc":26},
        {"id":"EQ-013","title":"Safe Arrival","desc":"Complete a `!travel` mission","obj":"travel","req":1,"time_h":12,"type":"Daily","rep":55,"nc":220,"cc":22},
        {"id":"EQ-014","title":"Patrol Duty","desc":"Use `!explore` 5 times","obj":"explore","req":5,"time_h":24,"type":"Daily","rep":70,"nc":280,"cc":28},
        {"id":"EQ-015","title":"Challenge Seeker","desc":"`!fight` 3 players","obj":"fight","req":3,"time_h":24,"type":"Daily","rep":75,"nc":300,"cc":30},
        {"id":"EQ-016","title":"Path Clearer","desc":"Use `!explore` 30 times","obj":"explore","req":30,"time_h":168,"type":"Weekly","rep":280,"nc":1120,"cc":112},
        {"id":"EQ-017","title":"Weekly Warrior","desc":"Win 8 `!fight` duels","obj":"fight_win","req":8,"time_h":168,"type":"Weekly","rep":300,"nc":1200,"cc":120},
        {"id":"EQ-018","title":"Consistent Earner","desc":"Use `!hourly` 20 times","obj":"hourly","req":20,"time_h":168,"type":"Weekly","rep":270,"nc":1080,"cc":108},
        {"id":"EQ-019","title":"The Long Haul","desc":"Complete 12 `!travel` missions","obj":"travel","req":12,"time_h":168,"type":"Weekly","rep":310,"nc":1240,"cc":124},
        {"id":"EQ-020","title":"Rising Name","desc":"Win 4 `!fight` duels","obj":"fight_win","req":4,"time_h":168,"type":"Weekly","rep":320,"nc":1280,"cc":128},
    ],
    "D": [
        {"id":"DQ-001","title":"Into the Wilds","desc":"Use `!explore` 12 times","obj":"explore","req":12,"time_h":24,"type":"Daily","rep":80,"nc":320,"cc":32},
        {"id":"DQ-002","title":"The Apothecary's Order","desc":"Gather 15 medicinal herbs","obj":"gather","req":15,"time_h":24,"type":"Daily","rep":85,"nc":340,"cc":34},
        {"id":"DQ-003","title":"Road to the Capital","desc":"Complete 3 `!travel` missions","obj":"travel","req":3,"time_h":24,"type":"Daily","rep":90,"nc":360,"cc":36},
        {"id":"DQ-004","title":"Proving Grounds","desc":"Win 3 `!fight` duels","obj":"fight_win","req":3,"time_h":24,"type":"Daily","rep":95,"nc":380,"cc":38},
        {"id":"DQ-005","title":"Arc I — Bandit Skirmish","desc":"Win 1 Arc I battle","obj":"arc_win_1","req":1,"time_h":24,"type":"Daily","rep":110,"nc":440,"cc":44},
        {"id":"DQ-006","title":"Arc I — Road Ambush","desc":"Win 2 Arc I battles","obj":"arc_win_1","req":2,"time_h":24,"type":"Daily","rep":120,"nc":480,"cc":48},
        {"id":"DQ-007","title":"Entry Raid","desc":"Defeat a raid boss once","obj":"raid_defeat","req":1,"time_h":48,"type":"Daily","rep":150,"nc":600,"cc":60},
        {"id":"DQ-008","title":"Hourly Grind","desc":"Use `!hourly` 7 times","obj":"hourly","req":7,"time_h":24,"type":"Daily","rep":70,"nc":280,"cc":28},
        {"id":"DQ-009","title":"Challenge Circuit","desc":"`!fight` 5 players","obj":"fight","req":5,"time_h":24,"type":"Daily","rep":130,"nc":520,"cc":52},
        {"id":"DQ-010","title":"Deep Exploration","desc":"Use `!explore` 25 times","obj":"explore","req":25,"time_h":120,"type":"Weekly","rep":400,"nc":1600,"cc":160},
        {"id":"DQ-011","title":"Mass Harvest","desc":"Gather 60 medicinal herbs","obj":"gather","req":60,"time_h":168,"type":"Weekly","rep":420,"nc":1680,"cc":168},
        {"id":"DQ-012","title":"Delivery Marathon","desc":"Complete 15 `!travel` missions","obj":"travel","req":15,"time_h":168,"type":"Weekly","rep":440,"nc":1760,"cc":176},
        {"id":"DQ-013","title":"Fighter's Week","desc":"Win 12 `!fight` duels","obj":"fight_win","req":12,"time_h":168,"type":"Weekly","rep":460,"nc":1840,"cc":184},
        {"id":"DQ-014","title":"Arc I Cleared","desc":"Win 5 Arc I battles","obj":"arc_win_1","req":5,"time_h":168,"type":"Weekly","rep":500,"nc":2000,"cc":200},
        {"id":"DQ-015","title":"Raid Repeat","desc":"Defeat a raid boss 3 times","obj":"raid_defeat","req":3,"time_h":168,"type":"Weekly","rep":550,"nc":2200,"cc":220},
        {"id":"DQ-016","title":"Disciplined Soldier","desc":"Use `!hourly` 20 times","obj":"hourly","req":20,"time_h":168,"type":"Weekly","rep":380,"nc":1520,"cc":152},
        {"id":"DQ-017","title":"Wandering Blade","desc":"Win 2 `!fight` duels","obj":"fight_win","req":2,"time_h":24,"type":"Daily","rep":170,"nc":680,"cc":68},
        {"id":"DQ-018","title":"Herb Specialist","desc":"Gather 20 medicinal herbs","obj":"gather","req":20,"time_h":48,"type":"Daily","rep":160,"nc":640,"cc":64},
        {"id":"DQ-019","title":"Endurance Run","desc":"Use `!explore` 35 times","obj":"explore","req":35,"time_h":168,"type":"Weekly","rep":480,"nc":1920,"cc":192},
        {"id":"DQ-020","title":"The Good Name","desc":"Win 6 `!fight` duels","obj":"fight_win","req":6,"time_h":168,"type":"Weekly","rep":520,"nc":2080,"cc":208},
    ],
    "C": [
        {"id":"CQ-001","title":"Arc II — The Collapsed Mine","desc":"Win 1 Arc II battle","obj":"arc_win_2","req":1,"time_h":24,"type":"Daily","rep":200,"nc":800,"cc":80},
        {"id":"CQ-002","title":"Arc II — Saving the Village","desc":"Win 2 Arc II battles","obj":"arc_win_2","req":2,"time_h":48,"type":"Daily","rep":220,"nc":880,"cc":88},
        {"id":"CQ-003","title":"Beast Hunt","desc":"Defeat a raid boss once","obj":"raid_defeat","req":1,"time_h":48,"type":"Daily","rep":250,"nc":1000,"cc":100},
        {"id":"CQ-004","title":"Seasoned Fighter","desc":"Win 5 `!fight` duels","obj":"fight_win","req":5,"time_h":24,"type":"Daily","rep":210,"nc":840,"cc":84},
        {"id":"CQ-005","title":"Deep Roots","desc":"Gather 20 medicinal herbs","obj":"gather","req":20,"time_h":24,"type":"Daily","rep":180,"nc":720,"cc":72},
        {"id":"CQ-006","title":"City Run","desc":"Complete 4 `!travel` missions","obj":"travel","req":4,"time_h":24,"type":"Daily","rep":190,"nc":760,"cc":76},
        {"id":"CQ-007","title":"Explorer's Instinct","desc":"Use `!explore` 15 times","obj":"explore","req":15,"time_h":24,"type":"Daily","rep":175,"nc":700,"cc":70},
        {"id":"CQ-008","title":"Clockwork","desc":"Use `!hourly` 8 times","obj":"hourly","req":8,"time_h":24,"type":"Daily","rep":160,"nc":640,"cc":64},
        {"id":"CQ-009","title":"Rival Duel","desc":"Win 3 `!fight` duels","obj":"fight_win","req":3,"time_h":24,"type":"Daily","rep":270,"nc":1080,"cc":108},
        {"id":"CQ-010","title":"Arc II Full Clear","desc":"Win 5 Arc II battles","obj":"arc_win_2","req":5,"time_h":168,"type":"Weekly","rep":800,"nc":3200,"cc":320},
        {"id":"CQ-011","title":"Boss Week","desc":"Defeat a raid boss 4 times","obj":"raid_defeat","req":4,"time_h":168,"type":"Weekly","rep":900,"nc":3600,"cc":360},
        {"id":"CQ-012","title":"Duellist's Record","desc":"Win 18 `!fight` duels","obj":"fight_win","req":18,"time_h":168,"type":"Weekly","rep":850,"nc":3400,"cc":340},
        {"id":"CQ-013","title":"Nature's Bounty","desc":"Gather 80 medicinal herbs","obj":"gather","req":80,"time_h":168,"type":"Weekly","rep":780,"nc":3120,"cc":312},
        {"id":"CQ-014","title":"Veteran Traveller","desc":"Complete 20 `!travel` missions","obj":"travel","req":20,"time_h":168,"type":"Weekly","rep":820,"nc":3280,"cc":328},
        {"id":"CQ-015","title":"Charting the Unknown","desc":"Use `!explore` 45 times","obj":"explore","req":45,"time_h":168,"type":"Weekly","rep":760,"nc":3040,"cc":304},
        {"id":"CQ-016","title":"Time Investment","desc":"Use `!hourly` 25 times","obj":"hourly","req":25,"time_h":168,"type":"Weekly","rep":720,"nc":2880,"cc":288},
        {"id":"CQ-017","title":"Arc II — The Warden","desc":"Win 3 Arc II battles","obj":"arc_win_2","req":3,"time_h":72,"type":"Daily","rep":350,"nc":1400,"cc":140},
        {"id":"CQ-018","title":"Marked Man","desc":"Win 2 `!fight` duels","obj":"fight_win","req":2,"time_h":24,"type":"Daily","rep":230,"nc":920,"cc":92},
        {"id":"CQ-019","title":"Resilient","desc":"Use `!explore` 25 times","obj":"explore","req":25,"time_h":168,"type":"Weekly","rep":600,"nc":2400,"cc":240},
        {"id":"CQ-020","title":"C-Rank Legend","desc":"Win 8 `!fight` duels","obj":"fight_win","req":8,"time_h":168,"type":"Weekly","rep":950,"nc":3800,"cc":380},
    ],
    "B": [
        {"id":"BQ-001","title":"Arc III — The Siege","desc":"Win 1 Arc III battle","obj":"arc_win_3","req":1,"time_h":48,"type":"Daily","rep":400,"nc":1600,"cc":160},
        {"id":"BQ-002","title":"Arc III — Fallen Fortress","desc":"Win 3 Arc III battles","obj":"arc_win_3","req":3,"time_h":48,"type":"Daily","rep":420,"nc":1680,"cc":168},
        {"id":"BQ-003","title":"High Raid","desc":"Defeat a raid boss once","obj":"raid_defeat","req":1,"time_h":48,"type":"Daily","rep":500,"nc":2000,"cc":200},
        {"id":"BQ-004","title":"Tournament Circuit","desc":"Win 6 `!fight` duels","obj":"fight_win","req":6,"time_h":24,"type":"Daily","rep":380,"nc":1520,"cc":152},
        {"id":"BQ-005","title":"Lethal Herb","desc":"Gather 25 medicinal herbs","obj":"gather","req":25,"time_h":24,"type":"Daily","rep":320,"nc":1280,"cc":128},
        {"id":"BQ-006","title":"Express Delivery","desc":"Complete 5 `!travel` missions","obj":"travel","req":5,"time_h":24,"type":"Daily","rep":340,"nc":1360,"cc":136},
        {"id":"BQ-007","title":"Deep Dive","desc":"Use `!explore` 20 times","obj":"explore","req":20,"time_h":24,"type":"Daily","rep":360,"nc":1440,"cc":144},
        {"id":"BQ-008","title":"Clockwork Elite","desc":"Use `!hourly` 10 times","obj":"hourly","req":10,"time_h":24,"type":"Daily","rep":300,"nc":1200,"cc":120},
        {"id":"BQ-009","title":"Arc III — The General","desc":"Win 2 Arc III battles","obj":"arc_win_3","req":2,"time_h":72,"type":"Daily","rep":550,"nc":2200,"cc":220},
        {"id":"BQ-010","title":"Raid Chain","desc":"Defeat a raid boss 5 times","obj":"raid_defeat","req":5,"time_h":168,"type":"Weekly","rep":1500,"nc":6000,"cc":600},
        {"id":"BQ-011","title":"Arc III Full Clear","desc":"Win 6 Arc III battles","obj":"arc_win_3","req":6,"time_h":168,"type":"Weekly","rep":1600,"nc":6400,"cc":640},
        {"id":"BQ-012","title":"PvP Dominator","desc":"Win 25 `!fight` duels","obj":"fight_win","req":25,"time_h":168,"type":"Weekly","rep":1400,"nc":5600,"cc":560},
        {"id":"BQ-013","title":"Herb Mountain","desc":"Gather 100 medicinal herbs","obj":"gather","req":100,"time_h":168,"type":"Weekly","rep":1200,"nc":4800,"cc":480},
        {"id":"BQ-014","title":"Road Warrior","desc":"Complete 25 `!travel` missions","obj":"travel","req":25,"time_h":168,"type":"Weekly","rep":1250,"nc":5000,"cc":500},
        {"id":"BQ-015","title":"Uncharted","desc":"Use `!explore` 60 times","obj":"explore","req":60,"time_h":168,"type":"Weekly","rep":1300,"nc":5200,"cc":520},
        {"id":"BQ-016","title":"The Grind","desc":"Use `!hourly` 30 times","obj":"hourly","req":30,"time_h":168,"type":"Weekly","rep":1100,"nc":4400,"cc":440},
        {"id":"BQ-017","title":"Upward Spiral","desc":"Win 4 `!fight` duels","obj":"fight_win","req":4,"time_h":24,"type":"Daily","rep":600,"nc":2400,"cc":240},
        {"id":"BQ-018","title":"Raid Clean Sweep","desc":"Defeat a raid boss 2 times","obj":"raid_defeat","req":2,"time_h":168,"type":"Weekly","rep":1700,"nc":6800,"cc":680},
        {"id":"BQ-019","title":"Endurance Master","desc":"Use `!explore` 40 times","obj":"explore","req":40,"time_h":168,"type":"Weekly","rep":1800,"nc":7200,"cc":720},
        {"id":"BQ-020","title":"B-Rank Pinnacle","desc":"Win 10 `!fight` duels","obj":"fight_win","req":10,"time_h":168,"type":"Weekly","rep":2000,"nc":8000,"cc":800},
    ],
    "A": [
        {"id":"AQ-001","title":"Arc IV — The Kingdom's Ruin","desc":"Win 1 Arc IV battle","obj":"arc_win_4","req":1,"time_h":72,"type":"Daily","rep":700,"nc":2800,"cc":280},
        {"id":"AQ-002","title":"Arc IV — The Dragon's Keep","desc":"Win 4 Arc IV battles","obj":"arc_win_4","req":4,"time_h":72,"type":"Daily","rep":750,"nc":3000,"cc":300},
        {"id":"AQ-003","title":"Legendary Raid","desc":"Defeat a raid boss once","obj":"raid_defeat","req":1,"time_h":72,"type":"Daily","rep":900,"nc":3600,"cc":360},
        {"id":"AQ-004","title":"Elite Circuit","desc":"Win 8 `!fight` duels","obj":"fight_win","req":8,"time_h":24,"type":"Daily","rep":650,"nc":2600,"cc":260},
        {"id":"AQ-005","title":"Rare Harvest","desc":"Gather 30 medicinal herbs","obj":"gather","req":30,"time_h":24,"type":"Daily","rep":580,"nc":2320,"cc":232},
        {"id":"AQ-006","title":"Priority Delivery","desc":"Complete 6 `!travel` missions","obj":"travel","req":6,"time_h":24,"type":"Daily","rep":600,"nc":2400,"cc":240},
        {"id":"AQ-007","title":"Frontier","desc":"Use `!explore` 25 times","obj":"explore","req":25,"time_h":24,"type":"Daily","rep":620,"nc":2480,"cc":248},
        {"id":"AQ-008","title":"Unceasing","desc":"Use `!hourly` 12 times","obj":"hourly","req":12,"time_h":24,"type":"Daily","rep":540,"nc":2160,"cc":216},
        {"id":"AQ-009","title":"Arc IV — The Fallen King","desc":"Win 3 Arc IV battles","obj":"arc_win_4","req":3,"time_h":96,"type":"Daily","rep":1100,"nc":4400,"cc":440},
        {"id":"AQ-010","title":"Raid Annihilation","desc":"Defeat a raid boss 6 times","obj":"raid_defeat","req":6,"time_h":168,"type":"Weekly","rep":2500,"nc":10000,"cc":1000},
        {"id":"AQ-011","title":"Arc IV Complete","desc":"Win 8 Arc IV battles","obj":"arc_win_4","req":8,"time_h":168,"type":"Weekly","rep":2800,"nc":11200,"cc":1120},
        {"id":"AQ-012","title":"King of Duels","desc":"Win 30 `!fight` duels","obj":"fight_win","req":30,"time_h":168,"type":"Weekly","rep":2400,"nc":9600,"cc":960},
        {"id":"AQ-013","title":"Alchemist's Dream","desc":"Gather 120 medicinal herbs","obj":"gather","req":120,"time_h":168,"type":"Weekly","rep":2200,"nc":8800,"cc":880},
        {"id":"AQ-014","title":"Relentless Runner","desc":"Complete 30 `!travel` missions","obj":"travel","req":30,"time_h":168,"type":"Weekly","rep":2300,"nc":9200,"cc":920},
        {"id":"AQ-015","title":"World's Edge","desc":"Use `!explore` 75 times","obj":"explore","req":75,"time_h":168,"type":"Weekly","rep":2350,"nc":9400,"cc":940},
        {"id":"AQ-016","title":"Iron Clock","desc":"Use `!hourly` 35 times","obj":"hourly","req":35,"time_h":168,"type":"Weekly","rep":2000,"nc":8000,"cc":800},
        {"id":"AQ-017","title":"Giant Slayer","desc":"Win 5 `!fight` duels","obj":"fight_win","req":5,"time_h":24,"type":"Daily","rep":1200,"nc":4800,"cc":480},
        {"id":"AQ-018","title":"Full Sweep","desc":"Defeat a raid boss 3 times","obj":"raid_defeat","req":3,"time_h":168,"type":"Weekly","rep":3000,"nc":12000,"cc":1200},
        {"id":"AQ-019","title":"Relentless","desc":"Use `!explore` 50 times","obj":"explore","req":50,"time_h":168,"type":"Weekly","rep":3200,"nc":12800,"cc":1280},
        {"id":"AQ-020","title":"A-Rank Sovereign","desc":"Win 12 `!fight` duels","obj":"fight_win","req":12,"time_h":168,"type":"Weekly","rep":3500,"nc":14000,"cc":1400},
    ],
    "S": [
        {"id":"SQ-001","title":"Arc V — The God's Trial","desc":"Win 1 Arc V battle","obj":"arc_win_5","req":1,"time_h":96,"type":"Daily","rep":1500,"nc":6000,"cc":600},
        {"id":"SQ-002","title":"Arc V — Void Gate","desc":"Win 5 Arc V battles","obj":"arc_win_5","req":5,"time_h":96,"type":"Daily","rep":1600,"nc":6400,"cc":640},
        {"id":"SQ-003","title":"World Raid","desc":"Defeat a raid boss once","obj":"raid_defeat","req":1,"time_h":96,"type":"Daily","rep":2000,"nc":8000,"cc":800},
        {"id":"SQ-004","title":"Apex Duelist","desc":"Win 10 `!fight` duels","obj":"fight_win","req":10,"time_h":24,"type":"Daily","rep":1200,"nc":4800,"cc":480},
        {"id":"SQ-005","title":"Grand Harvest","desc":"Gather 40 medicinal herbs","obj":"gather","req":40,"time_h":24,"type":"Daily","rep":1000,"nc":4000,"cc":400},
        {"id":"SQ-006","title":"Legendary Courier","desc":"Complete 8 `!travel` missions","obj":"travel","req":8,"time_h":24,"type":"Daily","rep":1100,"nc":4400,"cc":440},
        {"id":"SQ-007","title":"Beyond the Horizon","desc":"Use `!explore` 30 times","obj":"explore","req":30,"time_h":24,"type":"Daily","rep":1050,"nc":4200,"cc":420},
        {"id":"SQ-008","title":"Infinite Clock","desc":"Use `!hourly` 15 times","obj":"hourly","req":15,"time_h":24,"type":"Daily","rep":900,"nc":3600,"cc":360},
        {"id":"SQ-009","title":"Arc V — The Final God","desc":"Win 3 Arc V battles","obj":"arc_win_5","req":3,"time_h":120,"type":"Daily","rep":3000,"nc":12000,"cc":1200},
        {"id":"SQ-010","title":"World Raid Domination","desc":"Defeat a raid boss 7 times","obj":"raid_defeat","req":7,"time_h":168,"type":"Weekly","rep":5000,"nc":20000,"cc":2000},
        {"id":"SQ-011","title":"Arc V: God Slayer","desc":"Win 8 Arc V battles","obj":"arc_win_5","req":8,"time_h":168,"type":"Weekly","rep":6000,"nc":24000,"cc":2400},
        {"id":"SQ-012","title":"Unconquered","desc":"Win 40 `!fight` duels","obj":"fight_win","req":40,"time_h":168,"type":"Weekly","rep":5500,"nc":22000,"cc":2200},
        {"id":"SQ-013","title":"Living Legend","desc":"Gather 150 medicinal herbs","obj":"gather","req":150,"time_h":168,"type":"Weekly","rep":4500,"nc":18000,"cc":1800},
        {"id":"SQ-014","title":"Phantom Road","desc":"Complete 40 `!travel` missions","obj":"travel","req":40,"time_h":168,"type":"Weekly","rep":4800,"nc":19200,"cc":1920},
        {"id":"SQ-015","title":"The Endless Path","desc":"Use `!explore` 100 times","obj":"explore","req":100,"time_h":168,"type":"Weekly","rep":5200,"nc":20800,"cc":2080},
        {"id":"SQ-016","title":"God's Schedule","desc":"Use `!hourly` 40 times","obj":"hourly","req":40,"time_h":168,"type":"Weekly","rep":4000,"nc":16000,"cc":1600},
        {"id":"SQ-017","title":"Mythic Slayer","desc":"Win 15 `!fight` duels","obj":"fight_win","req":15,"time_h":24,"type":"Daily","rep":3500,"nc":14000,"cc":1400},
        {"id":"SQ-018","title":"Season's Champion","desc":"Win 20 `!fight` duels","obj":"fight_win","req":20,"time_h":168,"type":"Weekly","rep":8000,"nc":32000,"cc":3200},
        {"id":"SQ-019","title":"Unstoppable","desc":"Use `!explore` 60 times","obj":"explore","req":60,"time_h":168,"type":"Weekly","rep":7000,"nc":28000,"cc":2800},
        {"id":"SQ-020","title":"The Immortal Name","desc":"Win 25 `!fight` duels","obj":"fight_win","req":25,"time_h":168,"type":"Weekly","rep":10000,"nc":40000,"cc":4000},
    ],
}

ALL_QUESTS_FLAT = {q["id"]: q for rank_quests in QUESTS.values() for q in rank_quests}

ACCEPT_LINES = [
    "*The Guild Receptionist slides a parchment across the desk, her expression stern.*\n\"This task is suited for an adventurer of your standing. Do not bring shame upon the guild. Take the contract, complete the deed, and return here for your reward.\"",
    "*She stamps your guild card and gestures towards the door.*\n\"The job is yours. Failure is not an option — the guild's reputation rests on yours.\"",
    "*Without looking up from her ledger, she slides the contract your way.*\n\"Accepted. Clock's ticking, adventurer. Don't waste time standing there.\"",
    "*She meets your eyes for a moment, then nods.*\n\"A sensible choice. Complete it with honor and the guild will reward you accordingly.\"",
    "*The receptionist raises an eyebrow, then approves the contract.*\n\"Ambitious. I like that. Prove you deserve the rank you carry.\"",
]
REPORT_LINES = [
    "*She reviews the evidence, nods once, and stamps your card.*\n\"Contract fulfilled. Acceptable work. Your reward has been recorded.\"",
    "*The receptionist scans your report, quill poised.*\n\"Confirmed. Well done — I expected nothing less. Your reputation precedes you.\"",
    "*She closes the ledger and meets your gaze.*\n\"Quest complete. The guild acknowledges your service. Take your reward and rest.\"",
    "*Without ceremony, she marks the quest complete.*\n\"Done and dusted. The guild thanks you. Don't spend your reward all in one place.\"",
    "*She affixes a seal to your completed contract.*\n\"Another successful mission. The board will remember this. Impressive.\"",
]
RANKUP_LINES = [
    "*She stamps your guild card with the new insignia, sliding it across the desk without looking up.*\n\"Don't let the rank go to your head. The higher you climb, the harder the fall.\"",
    "*She studies your record carefully before finally nodding.*\n\"You've earned it. Welcome to your new rank. The guild is watching.\"",
    "*A rare smile crosses her face as she stamps your promotion.*\n\"Remarkable progress. Don't stop now — the world only gets harder from here.\"",
    "*She sets down her quill and looks at you directly.*\n\"Rank confirmed. This means more responsibility, not just privilege. Understood?\"",
]
FAIL_LINES = [
    "*The receptionist marks a black line through your contract, her quill scraping the parchment.*\n\"A failed contract is a stain on your record, adventurer. Do not make a habit of it.\"",
    "*She tears the contract in two without a word, then marks your file.*\n\"Failed. Your reputation suffers for this. I hope the next contract fares better.\"",
    "*A cold look. A slash through the paper.*\n\"The guild does not tolerate carelessness. Reputation lost. Try again — and succeed this time.\"",
]

TRAVEL_MONSTERS = [
    {"name": "Bandits", "atk": 200, "def": 80, "hp": 500},
    {"name": "Wild Wolf Pack", "atk": 180, "def": 60, "hp": 400},
    {"name": "Rogue Mercenary", "atk": 250, "def": 100, "hp": 600},
    {"name": "Goblin Raiders", "atk": 150, "def": 50, "hp": 350},
    {"name": "Corrupted Guard", "atk": 300, "def": 120, "hp": 700},
    {"name": "Cave Troll", "atk": 350, "def": 200, "hp": 900},
    {"name": "Highwayman", "atk": 220, "def": 90, "hp": 550},
    {"name": "Shadow Wraith", "atk": 280, "def": 70, "hp": 450},
]

def calculate_damage(atk, defense):
    return max(atk // 5, atk - defense // 2)

def get_visible_ranks(rank):
    idx = RANK_ORDER.index(rank)
    visible = set()
    if idx > 0:
        visible.add(RANK_ORDER[idx - 1])
    visible.add(rank)
    if idx < len(RANK_ORDER) - 1:
        visible.add(RANK_ORDER[idx + 1])
    return visible

def generate_board(rank):
    visible = get_visible_ranks(rank)
    pool = []
    for r in visible:
        pool.extend(QUESTS[r])
    return random.sample(pool, min(10, len(pool)))

def get_rank_icon(rank):
    return RANK_ICONS.get(rank, "❓")


class AdventurersGuild(commands.Cog, name="AdventurersGuild"):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self._quest_expiry_loop())

    async def _quest_expiry_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(600)
            try:
                all_players = players.all()
                now = time.time()
                for p in all_players:
                    active = p.get('active_quests', [])
                    if not active:
                        continue
                    uid = p['id']
                    updated_active = []
                    failed_any = False
                    rep_loss_total = 0
                    rank = p.get('guild_rank', 'F')
                    rep_loss = RANKS[rank]['rep_loss']
                    for q in active:
                        expires = q.get('expires_at', 0)
                        if now > expires:
                            failed_any = True
                            rep_loss_total += rep_loss
                        else:
                            updated_active.append(q)
                    if failed_any:
                        new_rep = max(0, p.get('guild_rep', 0) - rep_loss_total)
                        players.update({'active_quests': updated_active, 'guild_rep': new_rep}, Player.id == uid)
                        try:
                            user = self.bot.get_user(int(uid))
                            if user:
                                embed = discord.Embed(
                                    title="❌ Quest Failed!",
                                    description=f"One or more quests expired! Lost `{rep_loss_total}` Reputation.\n*{random.choice(FAIL_LINES)}*",
                                    color=0xFF4444)
                                await user.send(embed=embed)
                        except:
                            pass
            except:
                pass

    def _ensure_guild_fields(self, user_id):
        p = players.search(Player.id == user_id)
        if not p:
            return
        p = p[0]
        updates = {}
        if 'guild_rank' not in p:
            updates['guild_rank'] = 'F'
        if 'guild_rep' not in p:
            updates['guild_rep'] = 0
        if 'clan_coins' not in p:
            updates['clan_coins'] = 0
        if 'active_quests' not in p:
            updates['active_quests'] = []
        if 'quest_board' not in p:
            updates['quest_board'] = []
        if 'quest_board_refreshed' not in p:
            updates['quest_board_refreshed'] = 0
        if 'last_gather' not in p:
            updates['last_gather'] = 0
        if updates:
            players.update(updates, Player.id == user_id)

    @commands.group(name="guild", aliases=["g"], invoke_without_command=True)
    async def guild_cmd(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        self._ensure_guild_fields(user_id)
        p = players.search(Player.id == user_id)[0]
        rank = p.get('guild_rank', 'F')
        rep = p.get('guild_rep', 0)
        cc = p.get('clan_coins', 0)
        active = p.get('active_quests', [])
        rank_info = RANKS[rank]
        next_rank_idx = RANK_ORDER.index(rank) + 1
        next_rank = RANK_ORDER[next_rank_idx] if next_rank_idx < len(RANK_ORDER) else None
        rep_needed = RANKS[next_rank]['rep_req'] if next_rank else rank_info['rep_req']

        embed = discord.Embed(title=f"🏛️ Adventurer's Guild — {ctx.author.display_name}", color=GOLD)
        embed.add_field(name="🎖️ Rank", value=f"{get_rank_icon(rank)} **{rank}-Rank**", inline=True)
        embed.add_field(name="⭐ Reputation", value=f"`{rep:,}`", inline=True)
        embed.add_field(name="🪙 Clan Coins", value=f"`{cc:,}`", inline=True)
        if next_rank:
            needed = max(0, rep_needed - rep)
            embed.add_field(name="📈 Next Rank", value=f"{get_rank_icon(next_rank)} **{next_rank}-Rank** — `{needed:,}` Rep needed", inline=False)
        else:
            embed.add_field(name="📈 Rank", value="✨ **Maximum Rank Achieved!**", inline=False)
        embed.add_field(name="📋 Active Quests", value=f"`{len(active)}/{rank_info['max_active']}`", inline=True)
        embed.add_field(name="📅 Max Daily", value=f"`{rank_info['max_daily']}`", inline=True)
        embed.add_field(name="📆 Max Weekly", value=f"`{rank_info['max_weekly']}`", inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="📖 Commands",
            value="`!guild board` — View quest board\n`!accept <ID>` — Accept a quest\n`!abandon <ID>` — Abandon a quest\n`!report <ID>` — Report completed quest\n`!rankup` — Rank up when threshold met",
            inline=False)
        embed.set_footer(text="Nexworld RPG • Adventurer's Guild")
        await ctx.send(embed=embed)

    @guild_cmd.command(name="board")
    async def guild_board(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        self._ensure_guild_fields(user_id)
        p = players.search(Player.id == user_id)[0]
        rank = p.get('guild_rank', 'F')
        now = time.time()
        board = p.get('quest_board', [])
        refreshed = p.get('quest_board_refreshed', 0)

        if now - refreshed > 86400 or not board:
            board = generate_board(rank)
            players.update({'quest_board': board, 'quest_board_refreshed': now}, Player.id == user_id)

        track_quest_progress(user_id, 'guild_board', 1)

        active_ids = {q['quest_id'] for q in p.get('active_quests', [])}
        embed = discord.Embed(title="📋 Quest Board", color=GOLD)
        embed.description = f"*Showing quests for {get_rank_icon(rank)} **{rank}-Rank**. Refreshes every 24 hours.*"

        for q in board:
            status = "✅ Active" if q['id'] in active_ids else ""
            bar = "⬛" * 10
            embed.add_field(
                name=f"`{q['id']}` — {q['title']} [{q['type']}] {status}",
                value=(f"{q['desc']}\n"
                       f"⏰ `{q['time_h']}h` | 🎖️ `+{q['rep']} Rep` | 💰 `{q['nc']:,} NC` | 🪙 `{q['cc']} CC`\n"
                       f"Progress: `{bar}`"),
                inline=False)
        embed.set_footer(text="Use !accept <ID> to accept a quest • Nexworld RPG")
        await ctx.send(embed=embed)

    @commands.command(name="accept")
    async def accept_quest(self, ctx, quest_id: str = None):
        if not quest_id:
            await ctx.send(embed=discord.Embed(description="Usage: `!accept <QuestID>` — e.g. `!accept FQ-001`", color=GOLD))
            return
        quest_id = quest_id.upper()
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        self._ensure_guild_fields(user_id)
        p = players.search(Player.id == user_id)[0]

        quest_data = ALL_QUESTS_FLAT.get(quest_id)
        if not quest_data:
            await ctx.send(embed=discord.Embed(description=f"❌ Quest `{quest_id}` not found!", color=GOLD))
            return

        rank = p.get('guild_rank', 'F')
        visible = get_visible_ranks(rank)
        quest_rank = quest_id[0]
        if quest_rank not in visible:
            await ctx.send(embed=discord.Embed(description=f"❌ Your rank ({rank}) cannot accept this quest!", color=GOLD))
            return

        active = p.get('active_quests', [])
        max_active = RANKS[rank]['max_active']
        if len(active) >= max_active:
            await ctx.send(embed=discord.Embed(
                description=f"❌ You have too many active quests! (`{len(active)}/{max_active}`)\nAbandon one first with `!abandon <ID>`",
                color=GOLD))
            return

        if any(q['quest_id'] == quest_id for q in active):
            await ctx.send(embed=discord.Embed(description=f"❌ You already have quest `{quest_id}` active!", color=GOLD))
            return

        now = time.time()
        new_quest = {
            "quest_id": quest_id,
            "title": quest_data['title'],
            "objective_type": quest_data['obj'],
            "progress": 0,
            "required": quest_data['req'],
            "accepted_at": now,
            "expires_at": now + quest_data['time_h'] * 3600,
            "reward_nc": quest_data['nc'],
            "reward_rep": quest_data['rep'],
            "reward_cc": quest_data['cc'],
            "time_h": quest_data['time_h'],
            "type": quest_data['type'],
        }
        active.append(new_quest)
        players.update({'active_quests': active}, Player.id == user_id)

        flavor = random.choice(ACCEPT_LINES)
        embed = discord.Embed(title=f"📜 Quest Accepted: {quest_data['title']}", color=GOLD)
        embed.description = flavor
        embed.add_field(name="📋 Objective", value=quest_data['desc'], inline=False)
        expires_in = f"{quest_data['time_h']}h"
        embed.add_field(name="⏰ Time Limit", value=f"`{expires_in}`", inline=True)
        embed.add_field(name="🎖️ Rep Reward", value=f"`+{quest_data['rep']}`", inline=True)
        embed.add_field(name="💰 NC Reward", value=f"`{quest_data['nc']:,}`", inline=True)
        embed.add_field(name="🪙 CC Reward", value=f"`{quest_data['cc']}`", inline=True)
        embed.set_footer(text="Nexworld RPG • Adventurer's Guild")
        await ctx.send(embed=embed)

    @commands.command(name="abandon")
    async def abandon_quest(self, ctx, quest_id: str = None):
        if not quest_id:
            await ctx.send(embed=discord.Embed(description="Usage: `!abandon <QuestID>`", color=GOLD))
            return
        quest_id = quest_id.upper()
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        p = p[0]
        active = p.get('active_quests', [])
        quest = next((q for q in active if q['quest_id'] == quest_id), None)
        if not quest:
            await ctx.send(embed=discord.Embed(description=f"❌ No active quest `{quest_id}` found!", color=GOLD))
            return
        rank = p.get('guild_rank', 'F')
        rep_loss = RANKS[rank]['rep_loss']
        new_rep = max(0, p.get('guild_rep', 0) - rep_loss)
        active.remove(quest)
        players.update({'active_quests': active, 'guild_rep': new_rep}, Player.id == user_id)

        flavor = random.choice(FAIL_LINES)
        embed = discord.Embed(title=f"🗑️ Quest Abandoned: {quest['title']}", color=0xFF4444)
        embed.description = flavor
        embed.add_field(name="⚠️ Reputation Lost", value=f"`-{rep_loss}` (now `{new_rep:,}`)", inline=False)
        embed.set_footer(text="Nexworld RPG • Adventurer's Guild")
        await ctx.send(embed=embed)

    @commands.command(name="report")
    async def report_quest(self, ctx, quest_id: str = None):
        if not quest_id:
            await ctx.send(embed=discord.Embed(description="Usage: `!report <QuestID>`", color=GOLD))
            return
        quest_id = quest_id.upper()
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        p = p[0]
        active = p.get('active_quests', [])
        quest = next((q for q in active if q['quest_id'] == quest_id), None)
        if not quest:
            await ctx.send(embed=discord.Embed(description=f"❌ No active quest `{quest_id}` found!", color=GOLD))
            return

        if quest.get('progress', 0) < quest.get('required', 1):
            await ctx.send(embed=discord.Embed(
                description=(f"❌ Quest not complete yet!\n"
                             f"Progress: `{quest['progress']}/{quest['required']}`"),
                color=GOLD))
            return

        active.remove(quest)
        new_rep = p.get('guild_rep', 0) + quest['reward_rep']
        new_nc = p.get('nexcoins', 0) + quest['reward_nc']
        new_cc = p.get('clan_coins', 0) + quest['reward_cc']
        players.update({
            'active_quests': active,
            'guild_rep': new_rep,
            'nexcoins': new_nc,
            'clan_coins': new_cc,
        }, Player.id == user_id)

        update_clan_rep(user_id, quest['reward_rep'])
        track_quest_progress(user_id, 'quest_complete', 1)

        flavor = random.choice(REPORT_LINES)
        embed = discord.Embed(title=f"✅ Quest Complete: {quest['title']}", color=0x00CC66)
        embed.description = flavor
        embed.add_field(name="🎖️ Reputation", value=f"`+{quest['reward_rep']}` (now `{new_rep:,}`)", inline=True)
        embed.add_field(name="💰 Nexcoins", value=f"`+{quest['reward_nc']:,}`", inline=True)
        embed.add_field(name="🪙 Clan Coins", value=f"`+{quest['reward_cc']}`", inline=True)
        embed.set_footer(text="Nexworld RPG • Adventurer's Guild")
        await ctx.send(embed=embed)

    @commands.command(name="rankup")
    async def rankup(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        self._ensure_guild_fields(user_id)
        p = players.search(Player.id == user_id)[0]
        rank = p.get('guild_rank', 'F')
        rep = p.get('guild_rep', 0)

        if rank == 'S':
            await ctx.send(embed=discord.Embed(description="✨ You are already at **S-Rank** — the pinnacle!", color=GOLD))
            return

        next_idx = RANK_ORDER.index(rank) + 1
        next_rank = RANK_ORDER[next_idx]
        needed = RANKS[next_rank]['rep_req']
        if rep < needed:
            await ctx.send(embed=discord.Embed(
                description=(f"❌ Not enough Reputation to rank up!\n"
                             f"You need `{needed:,}` Rep • You have `{rep:,}`\n"
                             f"Still need `{needed - rep:,}` more!"),
                color=GOLD))
            return

        players.update({'guild_rank': next_rank, 'quest_board': [], 'quest_board_refreshed': 0}, Player.id == user_id)
        flavor = random.choice(RANKUP_LINES)
        embed = discord.Embed(title=f"🎉 Rank Up! {get_rank_icon(rank)} → {get_rank_icon(next_rank)}", color=0xFFD700)
        embed.description = flavor
        embed.add_field(name="New Rank", value=f"**{next_rank}-Rank** {get_rank_icon(next_rank)}", inline=True)
        embed.add_field(name="Reputation", value=f"`{rep:,}`", inline=True)
        embed.add_field(name="Daily Quest Limit", value=f"`{RANKS[next_rank]['max_daily']}`", inline=True)
        embed.set_footer(text="Nexworld RPG • Adventurer's Guild")
        await ctx.send(embed=embed)

    @commands.command(name="gather")
    async def gather(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        self._ensure_guild_fields(user_id)
        p = players.search(Player.id == user_id)[0]

        active = p.get('active_quests', [])
        gather_quest = next((q for q in active if q.get('objective_type') == 'gather'), None)
        if not gather_quest:
            await ctx.send(embed=discord.Embed(
                description="❌ You don't have an active gathering quest!\nAccept one from `!guild board` first.",
                color=GOLD))
            return

        now = time.time()
        last = p.get('last_gather', 0)
        cooldown = 300
        if now - last < cooldown:
            remaining = int(cooldown - (now - last))
            m, s = divmod(remaining, 60)
            await ctx.send(embed=discord.Embed(
                description=f"⏳ Gathering cooldown! Come back in **{m}m {s}s**.",
                color=GOLD))
            return

        players.update({'last_gather': now}, Player.id == user_id)
        completed = track_quest_progress(user_id, 'gather', 1)

        p2 = players.search(Player.id == user_id)[0]
        quest_now = next((q for q in p2.get('active_quests', []) if q['quest_id'] == gather_quest['quest_id']), gather_quest)
        prog = quest_now.get('progress', 0)
        req = quest_now.get('required', 1)

        herb_names = ["Moonpetal","Ashroot","Silverleaf","Ironmoss","Dawnbloom","Crimsonvine","Ghostweed","Sunbark","Emberfern","Hollowroot"]
        herb = random.choice(herb_names)
        embed = discord.Embed(title="🌿 Herb Gathered!", color=0x00AA55)
        embed.add_field(name="Found", value=f"**{herb}** (Medicinal Herb)", inline=True)
        embed.add_field(name="Quest Progress", value=f"`{prog}/{req}`", inline=True)
        if completed:
            embed.add_field(name="✅ Quest Ready!", value=f"Quest `{completed[0]}` complete! Use `!report {completed[0]}`", inline=False)
        embed.set_footer(text="Next gather in 5 minutes • Nexworld RPG")
        await ctx.send(embed=embed)

    @commands.command(name="travel")
    async def travel(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        self._ensure_guild_fields(user_id)
        p = players.search(Player.id == user_id)[0]

        monster = random.choice(TRAVEL_MONSTERS)
        p_atk = max(p.get('str', 10), p.get('mag', 10))
        p_def = p.get('def', 10)
        eq = p.get('equipped', {})
        inv_map = {i['uid']: i for i in p.get('inventory', []) if isinstance(i.get('uid'), str)}
        for slot in ['weapon', 'body_armor', 'head_armor']:
            uid = eq.get(slot)
            if uid and isinstance(uid, str) and uid in inv_map:
                stats = inv_map[uid].get('stats', {})
                p_atk += stats.get('str', 0) + stats.get('mag', 0)
                p_def += stats.get('def', 0)

        p_hp = p.get('hp', 100)
        m_hp = monster['hp']
        log = []
        for rnd in range(1, 8):
            p_dmg = calculate_damage(p_atk, monster['def'])
            m_dmg = calculate_damage(monster['atk'], p_def)
            m_hp -= p_dmg
            p_hp -= m_dmg
            log.append(f"**R{rnd}**: You `{p_dmg}` | {monster['name']} `{m_dmg}`")
            if m_hp <= 0 or p_hp <= 0:
                break

        won = m_hp <= 0
        destinations = ["Capital City","Merchant's Road","Northern Pass","Silverport Harbor","The Dusty Crossroads","Eastern Watchtower","Forest Village","Mountain Outpost"]
        dest = random.choice(destinations)

        embed = discord.Embed(
            title=f"🗺️ Travel Mission — Delivery to {dest}",
            color=0x00CC66 if won else 0xFF4444)
        embed.add_field(name="⚔️ Encounter", value=f"**{monster['name']}** blocked the road!", inline=False)
        embed.add_field(name="📋 Battle Log", value="\n".join(log[-4:]), inline=False)

        if won:
            reward_nc = random.randint(300, 800)
            embed.add_field(name="✅ Mission Success!", value=f"The package was delivered safely!\n+`{reward_nc:,}` NC", inline=False)
            new_nc = p.get('nexcoins', 0) + reward_nc
            players.update({'nexcoins': new_nc}, Player.id == user_id)
            completed = track_quest_progress(user_id, 'travel', 1)
            if completed:
                embed.add_field(name="✅ Quest Ready!", value="\n".join(f"`!report {qid}`" for qid in completed), inline=False)
        else:
            embed.add_field(name="❌ Mission Failed!", value="You were driven back. The package was lost.", inline=False)

        embed.set_footer(text="Nexworld RPG • Adventurer's Guild")
        await ctx.send(embed=embed)

    @commands.command(name="myquests", aliases=["mq"])
    async def my_quests(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        self._ensure_guild_fields(user_id)
        p = players.search(Player.id == user_id)[0]
        active = p.get('active_quests', [])
        if not active:
            await ctx.send(embed=discord.Embed(description="📋 No active quests. Use `!guild board` to find one!", color=GOLD))
            return
        now = time.time()
        embed = discord.Embed(title="📋 Your Active Quests", color=GOLD)
        for q in active:
            prog = q.get('progress', 0)
            req = q.get('required', 1)
            bar_filled = int((prog / req) * 10) if req > 0 else 0
            bar = "🟩" * bar_filled + "⬛" * (10 - bar_filled)
            remaining_s = max(0, int(q.get('expires_at', 0) - now))
            h, rem = divmod(remaining_s, 3600)
            m = rem // 60
            status = "✅ READY" if prog >= req else f"{bar} `{prog}/{req}`"
            embed.add_field(
                name=f"`{q['quest_id']}` — {q['title']}",
                value=(f"Progress: {status}\n"
                       f"⏰ Expires in: `{h}h {m}m` | 🎖️ `+{q['reward_rep']} Rep`"),
                inline=False)
        embed.set_footer(text="Use !report <ID> when complete • Nexworld RPG")
        await ctx.send(embed=embed)


def update_clan_rep(user_id, amount):
    try:
        from tinydb import TinyDB, Query
        clan_db = TinyDB('clan_data.json')
        ClanQ = Query()
        clans = clan_db.search(ClanQ.members.any([user_id]))
        if clans:
            g = clans[0]
            clan_db.update({'total_rep': g.get('total_rep', 0) + amount}, ClanQ.name == g['name'])
    except:
        pass


async def setup(bot):
    await bot.add_cog(AdventurersGuild(bot))
