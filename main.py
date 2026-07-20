import discord
import os
from dotenv import load_dotenv
load_dotenv()
from discord.ext import commands
from tinydb import TinyDB, Query
import random
import time
import asyncio
from flask import Flask, request, jsonify
from threading import Thread

# ─── KEEP ALIVE ───
app = Flask('')

@app.route('/')
def home():
    return "Nexworld is alive!"

@app.route('/vote-webhook', methods=['POST'])
def vote_webhook():
    auth = request.headers.get('Authorization')
    expected = os.getenv('TOPGG_WEBHOOK_SECRET')
    if not expected or auth != expected:
        return jsonify({'error': 'unauthorized'}), 401
    data = request.json or {}
    user_id = str(data.get('user', ''))
    if not user_id:
        return jsonify({'error': 'no user'}), 400
    try:
        asyncio.run_coroutine_threadsafe(handle_vote(user_id), bot.loop)
    except Exception as e:
        print(f"Vote webhook error: {e}")
    return jsonify({'success': True}), 200

async def handle_vote(user_id):
    p = players.search(Player.id == user_id)
    if not p:
        return
    p = p[0]
    now = time.time()
    last_vote = p.get('last_vote', 0)
    streak = p.get('vote_streak', 0)
    if now - last_vote > 129600:
        streak = 0
    streak += 1
    votes = p.get('votes', 0) + 1

    streak_rewards = {1: 25000, 2: 30000, 3: 35000, 4: 40000, 5: 45000, 6: 50000}
    coin_reward = streak_rewards.get(streak, 60000)
    ss_gained = 10 if random.random() < 0.4 else 0

    new_coins = p.get('nexcoins', 0) + coin_reward
    new_ss = p.get('starshards', 0) + ss_gained

    players.update({
        'votes': votes,
        'vote_streak': streak,
        'last_vote': now,
        'nexcoins': new_coins,
        'starshards': new_ss,
        'vote_reminder_sent': False
    }, Player.id == user_id)

    try:
        user = bot.get_user(int(user_id))
        if user:
            embed = discord.Embed(title="🗳️ Vote Reward!", color=GOLD)
            embed.add_field(name="💰 Nexcoins", value=f"+{coin_reward:,}", inline=True)
            embed.add_field(name="🔥 Streak", value=f"x{streak}", inline=True)
            if ss_gained:
                embed.add_field(name="✨ Starshards", value=f"+{ss_gained}", inline=True)
            embed.set_footer(text="Nexworld RPG • Thanks for voting!")
            await user.send(embed=embed)
    except Exception:
        pass

def run():
    app.run(host='0.0.0.0', port=8080)

keep_alive_thread = Thread(target=run)
keep_alive_thread.daemon = True
keep_alive_thread.start()

# ─── DATABASE ───
from db import db, players, prefixes_table, market_table, raids_table, Player, Prefix

# ─── CONSTANTS ───
GOLD = 0xFFD700
ALLOWED_PREFIXES = ['!', '$', '-', '*', '?', '.']
ADMIN_IDS = ["954487623462813757"]

# ─── RACES ───
RACES = {
    "Human":     {"rarity": "Common",    "rarity_icon": "⭐", "chance": "30%", "hp": 100, "str": 10, "mag": 10, "def": 10},
    "Halfblood": {"rarity": "Common",    "rarity_icon": "⭐", "chance": "25%", "hp": 100, "str": 10, "mag": 14, "def": 11},
    "Kobold":    {"rarity": "Common",    "rarity_icon": "⭐", "chance": "25%", "hp": 100, "str": 10, "mag": 8,  "def": 11},
    "Elf":       {"rarity": "Rare",      "rarity_icon": "💎", "chance": "10%", "hp": 120, "str": 12, "mag": 20, "def": 13},
    "Beastkin":  {"rarity": "Rare",      "rarity_icon": "💎", "chance": "7%",  "hp": 140, "str": 18, "mag": 8,  "def": 15},
    "Dragon-kin":{"rarity": "Primordial","rarity_icon": "👑", "chance": "2%",  "hp": 200, "str": 30, "mag": 18, "def": 30},
    "Seraphim":  {"rarity": "Primordial","rarity_icon": "👑", "chance": "1%",  "hp": 200, "str": 25, "mag": 30, "def": 25},
}

# ─── RACE POOLS ───
RACE_POOL_NORMAL = (
    ["Human"] * 300 + ["Halfblood"] * 250 + ["Kobold"] * 250 +
    ["Elf"] * 120 + ["Beastkin"] * 75 + ["Dragon-kin"] * 4 + ["Seraphim"] * 1
)
RACE_POOL_REINCARNATION = (
    ["Elf"] * 450 + ["Beastkin"] * 400 + ["Dragon-kin"] * 120 + ["Seraphim"] * 30
)
RACE_POOL_TELEPORTED = (
    ["Dragon-kin"] * 200 + ["Seraphim"] * 150 + ["Beastkin"] * 350 + ["Elf"] * 300
)
RACE_POOL_REROLL = (
    ["Elf"] * 450 + ["Beastkin"] * 400 + ["Dragon-kin"] * 120 + ["Seraphim"] * 30
)

# ─── ORIGINS ───
ORIGINS = ["Normal", "Reincarnation", "Teleported"]
ORIGIN_WEIGHTS = [65, 25, 10]
ORIGIN_ICONS = {
    "Normal": "🌱",
    "Reincarnation": "🔄",
    "Teleported": "⚡"
}
ORIGIN_TEXT = {
    "Normal": "You were born into this world like any other soul. A new life, a blank slate. Your story begins now.",
    "Reincarnation": "You remember it clearly — the moment your previous life ended. But fate wasn't done with you. You've been given another chance.",
    "Teleported": "One moment you were living your normal life. The next — you were ripped from your world without warning and thrown into this one."
}

# ─── SKILLS ───
RACE_SKILLS = {
    "Human": {
        "skills": [
            {"name": "Iron Strike", "evolutions": ["Iron Strike", "Steel Cleave", "Titan Slash", "World Cutter", "Omega Cleave"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Resilience", "evolutions": ["Resilience", "Second Wind", "Unyielding", "Indomitable", "Immortal Will"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Battle Cry", "evolutions": ["Battle Cry", "War Cry", "Warlord's Roar", "Conqueror's Call", "Legendary Cry"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Counter", "evolutions": ["Counter", "Counter Strike", "Deflect", "Retribution", "Omega Counter"], "evo_levels": [1, 100, 250, 500, 750]}
        ],
        "special": {"name": "Will of Humanity", "unlock_level": 10}
    },
    "Halfblood": {
        "skills": [
            {"name": "Arcane Strike", "evolutions": ["Arcane Strike", "Mystic Slash", "Void Strike", "Chaos Cleave", "Annihilation Strike"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Blood Surge", "evolutions": ["Blood Surge", "Blood Rush", "Blood Frenzy", "Crimson Rage", "Omega Surge"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Spellblade", "evolutions": ["Spellblade", "Enhanced Spellblade", "Runic Blade", "Chaos Blade", "Omega Spellblade"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Hybrid Shield", "evolutions": ["Hybrid Shield", "Arcane Guard", "Arcane Ward", "Chaos Shield", "Omega Ward"], "evo_levels": [1, 100, 250, 500, 750]}
        ],
        "special": {"name": "Blood and Magic", "unlock_level": 10}
    },
    "Kobold": {
        "skills": [
            {"name": "Sneak Attack", "evolutions": ["Sneak Attack", "Shadow Strike", "Void Stab", "Death Mark", "Omega Sneak"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Trap", "evolutions": ["Trap", "Reinforced Trap", "Venom Trap", "Death Trap", "Omega Trap"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Dodge", "evolutions": ["Dodge", "Swift Dodge", "Phantom Dodge", "Death Dodge", "Omega Dodge"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Poison Vial", "evolutions": ["Poison Vial", "Toxic Vial", "Venom Vial", "Death Vial", "Omega Poison"], "evo_levels": [1, 100, 250, 500, 750]}
        ],
        "special": {"name": "Death from Shadows", "unlock_level": 10}
    },
    "Elf": {
        "skills": [
            {"name": "Magic Arrow", "evolutions": ["Magic Arrow", "Arcane Arrow", "Void Arrow", "Star Arrow", "Omega Arrow"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Nature's Blessing", "evolutions": ["Nature's Blessing", "Forest Blessing", "Ancient Blessing", "Divine Blessing", "Omega Blessing"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Arcane Barrier", "evolutions": ["Arcane Barrier", "Mystic Barrier", "Void Barrier", "Star Barrier", "Omega Barrier"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Ancient Curse", "evolutions": ["Ancient Curse", "Void Curse", "Star Curse", "Ancient Hex", "Omega Curse"], "evo_levels": [1, 100, 250, 500, 750]}
        ],
        "special": {"name": "Arcane Apocalypse", "unlock_level": 10}
    },
    "Beastkin": {
        "skills": [
            {"name": "Savage Strike", "evolutions": ["Savage Strike", "Feral Slash", "Beast Cleave", "Predator Strike", "Omega Savage"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Primal Roar", "evolutions": ["Primal Roar", "Beast Roar", "Alpha Roar", "Predator Roar", "Omega Roar"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Feral Healing", "evolutions": ["Feral Healing", "Beast Healing", "Beast Regeneration", "Predator Regen", "Omega Regeneration"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Unleash", "evolutions": ["Unleash", "Feral Unleash", "Feral Rage", "Predator Rage", "Omega Unleash"], "evo_levels": [1, 100, 250, 500, 750]}
        ],
        "special": {"name": "Beast Awakening", "unlock_level": 10}
    },
    "Dragon-kin": {
        "skills": [
            {"name": "Dragon Breath", "evolutions": ["Dragon Breath", "Inferno Breath", "Ancient Breath", "Dragon's Fury", "Omega Breath"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Iron Scales", "evolutions": ["Iron Scales", "Steel Scales", "Dragon Scales", "Ancient Scales", "Omega Scales"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Tail Sweep", "evolutions": ["Tail Sweep", "Dragon Sweep", "Ancient Sweep", "Devastating Sweep", "Omega Sweep"], "evo_levels": [1, 100, 250, 500, 750]},
            {"name": "Dragon's Dominance", "evolutions": ["Dragon's Dominance", "Ancient Dominance", "Dragon God's Will", "Eternal Dominance", "Omega Dominance"], "evo_levels": [1, 100, 250, 500, 750]}
        ],
        "special": {"name": "Dragon God's Wrath", "unlock_level": 10}
    },
    "Seraphim": {
        "skills": [
            {"name": "Holy Strike", "evolutions": ["Holy Strike", "Sacred Strike", "Divine Strike", "Seraph's Wrath", "Omega Holy Strike"], "evo_levels": [1, 100, 250, 500, 750],
             "effects": [
                 {"type": "damage", "dmg_mult": 1.4},
                 {"type": "damage", "dmg_mult": 1.6},
                 {"type": "damage", "dmg_mult": 1.8},
                 {"type": "damage", "dmg_mult": 2.0},
                 {"type": "damage", "dmg_mult": 2.3}
             ]},
            {"name": "Divine Healing", "evolutions": ["Divine Healing", "Sacred Healing", "Holy Restoration", "Divine Restoration", "Omega Healing"], "evo_levels": [1, 100, 250, 500, 750],
             "effects": [
                 {"type": "heal_and_damage", "heal_pct": 0.50, "dmg_mult": 0.50},
                 {"type": "heal_and_damage", "heal_pct": 0.50, "dmg_mult": 0.65},
                 {"type": "heal_and_damage", "heal_pct": 0.50, "dmg_mult": 0.80},
                 {"type": "heal_and_damage", "heal_pct": 0.50, "dmg_mult": 0.95},
                 {"type": "heal_and_damage", "heal_pct": 0.50, "dmg_mult": 1.15}
             ]},
            {"name": "Wings of Light", "evolutions": ["Wings of Light", "Sacred Wings", "Divine Wings", "Seraph Wings", "Omega Wings"], "evo_levels": [1, 100, 250, 500, 750],
             "effects": [
                 {"type": "shield", "shield_pct": 0.15, "duration": 2},
                 {"type": "shield", "shield_pct": 0.20, "duration": 2},
                 {"type": "shield", "shield_pct": 0.25, "duration": 3},
                 {"type": "shield", "shield_pct": 0.32, "duration": 3},
                 {"type": "shield", "shield_pct": 0.40, "duration": 3}
             ]},
            {"name": "Judgment", "evolutions": ["Judgment", "Sacred Judgment", "Divine Judgment", "Seraph's Judgment", "Omega Judgment"], "evo_levels": [1, 100, 250, 500, 750],
             "effects": [
                 {"type": "pierce_damage", "dmg_mult": 1.8, "def_ignore_pct": 0.30},
                 {"type": "pierce_damage", "dmg_mult": 2.0, "def_ignore_pct": 0.40},
                 {"type": "pierce_damage", "dmg_mult": 2.3, "def_ignore_pct": 0.50},
                 {"type": "pierce_damage", "dmg_mult": 2.6, "def_ignore_pct": 0.65},
                 {"type": "pierce_damage", "dmg_mult": 3.0, "def_ignore_pct": 0.80}
             ]}
        ],
        "special": {"name": "Seraphic Purge", "unlock_level": 10,
                    "effect": {"type": "heal_and_damage", "heal_pct": 0.60, "dmg_mult": 3.0}}
    }
}

# ─── ARCS & ENEMIES ───
ARCS = {
    1: {
        "name": "Whispering Woods",
        "level_range": (1, 10),
        "enemies": [
            {"id": 1, "name": "Feral Slime", "rarity": "Common", "hp": 45, "atk": 12, "def": 5, "exp": (20, 40), "coins": (50, 150), "drop": "Slime Jelly"},
            {"id": 2, "name": "Forest Goblin", "rarity": "Common", "hp": 60, "atk": 18, "def": 8, "exp": (25, 45), "coins": (50, 150), "drop": "Rusty Dagger"},
            {"id": 3, "name": "Blighted Thorn-Vine", "rarity": "Common", "hp": 80, "atk": 14, "def": 12, "exp": (30, 50), "coins": (50, 150), "drop": "Sharp Thorn"},
            {"id": 4, "name": "Rabid Dire-Pup", "rarity": "Common", "hp": 55, "atk": 22, "def": 6, "exp": (30, 55), "coins": (50, 150), "drop": "Torn Fur"},
            {"id": 5, "name": "Giant Wood Spider", "rarity": "Uncommon", "hp": 70, "atk": 16, "def": 10, "exp": (40, 70), "coins": (150, 300), "drop": "Weak Venom Pod"},
            {"id": 6, "name": "Spore Shroom", "rarity": "Uncommon", "hp": 90, "atk": 11, "def": 15, "exp": (45, 80), "coins": (150, 300), "drop": "Luminescent Spores"},
        ]
    },
    2: {
        "name": "Sunken Catacombs",
        "level_range": (11, 25),
        "enemies": [
            {"id": 1, "name": "Decayed Skeleton", "rarity": "Common", "hp": 180, "atk": 45, "def": 25, "exp": (60, 100), "coins": (50, 150), "drop": "Ancient Bone"},
            {"id": 2, "name": "Crypt Ghoul", "rarity": "Common", "hp": 220, "atk": 55, "def": 18, "exp": (65, 110), "coins": (50, 150), "drop": "Putrid Flesh"},
            {"id": 3, "name": "Tomb Apparition", "rarity": "Uncommon", "hp": 150, "atk": 65, "def": 10, "exp": (80, 130), "coins": (150, 300), "drop": "Ectoplasm"},
            {"id": 4, "name": "Cavern Stone-Golem", "rarity": "Uncommon", "hp": 350, "atk": 35, "def": 60, "exp": (90, 140), "coins": (150, 300), "drop": "Iron Ore Fragment"},
            {"id": 5, "name": "Plague Rat Swarm", "rarity": "Uncommon", "hp": 160, "atk": 48, "def": 15, "exp": (85, 135), "coins": (150, 300), "drop": "Contaminated Tooth"},
            {"id": 6, "name": "Shadow Initiate", "rarity": "Rare", "hp": 200, "atk": 58, "def": 22, "exp": (100, 170), "coins": (300, 600), "drop": "Dark Cloth"},
            {"id": 7, "name": "Bone Wraith", "rarity": "Rare", "hp": 240, "atk": 62, "def": 28, "exp": (110, 180), "coins": (300, 600), "drop": "Wraith Essence"},
        ]
    },
    3: {"name": "Scorched Wastelands", "level_range": (26, 35), "enemies": [
        {"id": 1, "name": "Ash Salamander", "rarity": "Uncommon", "hp": 550, "atk": 120, "def": 75, "exp": (130, 200), "coins": (150, 300), "drop": "Fire Scale"},
        {"id": 2, "name": "Magma Imp", "rarity": "Uncommon", "hp": 420, "atk": 150, "def": 50, "exp": (140, 210), "coins": (150, 300), "drop": "Sulfuric Ash"},
        {"id": 3, "name": "Scorched Zealot", "rarity": "Rare", "hp": 600, "atk": 135, "def": 85, "exp": (160, 240), "coins": (300, 600), "drop": "Broken Talisman"},
        {"id": 4, "name": "Ember Hound", "rarity": "Rare", "hp": 580, "atk": 145, "def": 78, "exp": (165, 250), "coins": (300, 600), "drop": "Ember Core"},
        {"id": 5, "name": "Blazing Skull", "rarity": "Rare", "hp": 620, "atk": 155, "def": 80, "exp": (170, 260), "coins": (300, 600), "drop": "Skull Ash"},
        {"id": 6, "name": "Cinder Vulture", "rarity": "Rare", "hp": 480, "atk": 140, "def": 65, "exp": (175, 265), "coins": (300, 600), "drop": "Singed Feather"},
    ]},
    4: {"name": "Ashen Badlands", "level_range": (36, 45), "enemies": [
        {"id": 1, "name": "Dune Stalker", "rarity": "Rare", "hp": 500, "atk": 165, "def": 60, "exp": (190, 280), "coins": (300, 600), "drop": "Desert Carapace"},
        {"id": 2, "name": "Lava Slag", "rarity": "Rare", "hp": 750, "atk": 110, "def": 120, "exp": (200, 290), "coins": (300, 600), "drop": "Molten Core"},
        {"id": 3, "name": "Molten Golem", "rarity": "Rare", "hp": 820, "atk": 120, "def": 130, "exp": (210, 300), "coins": (300, 600), "drop": "Magma Stone"},
        {"id": 4, "name": "Ash Wraith", "rarity": "Rare", "hp": 680, "atk": 175, "def": 70, "exp": (215, 310), "coins": (300, 600), "drop": "Ash Fragment"},
        {"id": 5, "name": "Inferno Serpent", "rarity": "Epic", "hp": 900, "atk": 200, "def": 150, "exp": (250, 380), "coins": (600, 1200), "drop": "Serpent Scale"},
        {"id": 6, "name": "Charred Titan", "rarity": "Epic", "hp": 1100, "atk": 190, "def": 170, "exp": (260, 390), "coins": (600, 1200), "drop": "Titan Ash"},
        {"id": 7, "name": "Volcanic Drake", "rarity": "Epic", "hp": 1200, "atk": 210, "def": 160, "exp": (270, 400), "coins": (600, 1200), "drop": "Drake Scale"},
    ]},
    5: {"name": "Frozen Tundra", "level_range": (46, 60), "enemies": [
        {"id": 1, "name": "Frostbite Wolf", "rarity": "Rare", "hp": 1400, "atk": 380, "def": 180, "exp": (290, 420), "coins": (300, 600), "drop": "Winter Pelt"},
        {"id": 2, "name": "Ice-Crusted Zombie", "rarity": "Rare", "hp": 1900, "atk": 320, "def": 250, "exp": (300, 430), "coins": (300, 600), "drop": "Frozen Marrow"},
        {"id": 3, "name": "Glacial Sprite", "rarity": "Rare", "hp": 1100, "atk": 450, "def": 120, "exp": (310, 440), "coins": (300, 600), "drop": "Pristine Ice Shard"},
        {"id": 4, "name": "Snow Yeti Shaman", "rarity": "Epic", "hp": 2200, "atk": 360, "def": 220, "exp": (360, 520), "coins": (600, 1200), "drop": "Totem Fragment"},
        {"id": 5, "name": "Rime-Bound Armor", "rarity": "Epic", "hp": 2500, "atk": 290, "def": 400, "exp": (370, 530), "coins": (600, 1200), "drop": "Frigid Metal Scrap"},
        {"id": 6, "name": "Tundra Mammoth Calf", "rarity": "Epic", "hp": 3200, "atk": 410, "def": 300, "exp": (380, 540), "coins": (600, 1200), "drop": "Small Ivory Tusk"},
        {"id": 7, "name": "Blizzard Wraith", "rarity": "Epic", "hp": 2800, "atk": 430, "def": 280, "exp": (390, 550), "coins": (600, 1200), "drop": "Blizzard Essence"},
        {"id": 8, "name": "Frozen Banshee", "rarity": "Epic", "hp": 3000, "atk": 450, "def": 260, "exp": (400, 560), "coins": (600, 1200), "drop": "Banshee Shard"},
    ]},
    6: {"name": "Glacial Depths", "level_range": (61, 70), "enemies": [
        {"id": 1, "name": "Frost Golem", "rarity": "Epic", "hp": 3500, "atk": 480, "def": 350, "exp": (420, 600), "coins": (600, 1200), "drop": "Frost Core"},
        {"id": 2, "name": "Ice Serpent", "rarity": "Epic", "hp": 3200, "atk": 520, "def": 300, "exp": (430, 610), "coins": (600, 1200), "drop": "Ice Scale"},
        {"id": 3, "name": "Glacial Phantom", "rarity": "Epic", "hp": 2900, "atk": 560, "def": 280, "exp": (440, 620), "coins": (600, 1200), "drop": "Phantom Shard"},
        {"id": 4, "name": "Permafrost Elemental", "rarity": "Epic", "hp": 3800, "atk": 500, "def": 380, "exp": (450, 630), "coins": (600, 1200), "drop": "Permafrost Crystal"},
        {"id": 5, "name": "Frozen Revenant", "rarity": "Epic", "hp": 4000, "atk": 530, "def": 360, "exp": (460, 640), "coins": (600, 1200), "drop": "Revenant Ice"},
        {"id": 6, "name": "Tundra Colossus", "rarity": "Legendary", "hp": 5000, "atk": 600, "def": 450, "exp": (520, 750), "coins": (1200, 2500), "drop": "Colossus Fragment"},
        {"id": 7, "name": "Avalanche Beast", "rarity": "Legendary", "hp": 5500, "atk": 620, "def": 480, "exp": (540, 770), "coins": (1200, 2500), "drop": "Beast Core"},
    ]},
    7: {"name": "Sky Sanctuary", "level_range": (71, 80), "enemies": [
        {"id": 1, "name": "Sky-Guard Automaton", "rarity": "Epic", "hp": 6500, "atk": 1100, "def": 750, "exp": (560, 800), "coins": (600, 1200), "drop": "Rune Powered Gear"},
        {"id": 2, "name": "Corrupted Cherub", "rarity": "Epic", "hp": 5200, "atk": 1400, "def": 500, "exp": (570, 810), "coins": (600, 1200), "drop": "Defiled Feather"},
        {"id": 3, "name": "Storm Hawk", "rarity": "Epic", "hp": 5800, "atk": 1200, "def": 600, "exp": (580, 820), "coins": (600, 1200), "drop": "Storm Feather"},
        {"id": 4, "name": "Wind Specter", "rarity": "Legendary", "hp": 7000, "atk": 1350, "def": 700, "exp": (650, 920), "coins": (1200, 2500), "drop": "Wind Essence"},
        {"id": 5, "name": "Cloud Titan", "rarity": "Legendary", "hp": 8000, "atk": 1300, "def": 800, "exp": (660, 930), "coins": (1200, 2500), "drop": "Cloud Crystal"},
        {"id": 6, "name": "Thunder Wraith", "rarity": "Legendary", "hp": 7500, "atk": 1400, "def": 750, "exp": (670, 940), "coins": (1200, 2500), "drop": "Thunder Shard"},
        {"id": 7, "name": "Celestial Hound", "rarity": "Legendary", "hp": 8500, "atk": 1350, "def": 820, "exp": (680, 950), "coins": (1200, 2500), "drop": "Celestial Fang"},
        {"id": 8, "name": "Stormborn Knight", "rarity": "Legendary", "hp": 9000, "atk": 1450, "def": 850, "exp": (700, 970), "coins": (1200, 2500), "drop": "Storm Armor Shard"},
    ]},
    8: {"name": "Void Expanse", "level_range": (81, 90), "enemies": [
        {"id": 1, "name": "Void Tendril", "rarity": "Legendary", "hp": 7000, "atk": 1250, "def": 600, "exp": (720, 1000), "coins": (1200, 2500), "drop": "Essence of Void"},
        {"id": 2, "name": "Astral Phantom", "rarity": "Legendary", "hp": 4800, "atk": 1650, "def": 450, "exp": (730, 1010), "coins": (1200, 2500), "drop": "Star Dust Pile"},
        {"id": 3, "name": "Rift Walker", "rarity": "Legendary", "hp": 5900, "atk": 1500, "def": 550, "exp": (740, 1020), "coins": (1200, 2500), "drop": "Warp Crystal"},
        {"id": 4, "name": "Doomsday Cultist", "rarity": "Legendary", "hp": 8000, "atk": 1350, "def": 800, "exp": (750, 1030), "coins": (1200, 2500), "drop": "Forbidden Scroll"},
        {"id": 5, "name": "Void Shade", "rarity": "Legendary", "hp": 9000, "atk": 1500, "def": 850, "exp": (760, 1040), "coins": (1200, 2500), "drop": "Void Shard"},
        {"id": 6, "name": "Abyss Crawler", "rarity": "Legendary", "hp": 9500, "atk": 1550, "def": 900, "exp": (770, 1050), "coins": (1200, 2500), "drop": "Abyss Fragment"},
        {"id": 7, "name": "Null Entity", "rarity": "Legendary", "hp": 10000, "atk": 1600, "def": 950, "exp": (780, 1060), "coins": (1200, 2500), "drop": "Null Crystal"},
        {"id": 8, "name": "Void Reaper", "rarity": "Legendary", "hp": 10500, "atk": 1650, "def": 1000, "exp": (790, 1070), "coins": (1200, 2500), "drop": "Reaper Scythe Shard"},
        {"id": 9, "name": "Chaos Specter", "rarity": "Legendary", "hp": 11000, "atk": 1700, "def": 1050, "exp": (800, 1080), "coins": (1200, 2500), "drop": "Chaos Essence"},
    ]},
    9: {"name": "The Rift", "level_range": (91, 100), "enemies": [
        {"id": 1, "name": "Rift Guardian", "rarity": "Legendary", "hp": 12000, "atk": 1800, "def": 1100, "exp": (820, 1100), "coins": (1200, 2500), "drop": "Guardian Shard"},
        {"id": 2, "name": "Void Stalker", "rarity": "Legendary", "hp": 13000, "atk": 1900, "def": 1150, "exp": (830, 1110), "coins": (1200, 2500), "drop": "Stalker Fang"},
        {"id": 3, "name": "Abyssal Knight", "rarity": "Legendary", "hp": 14000, "atk": 2000, "def": 1200, "exp": (840, 1120), "coins": (1200, 2500), "drop": "Abyssal Armor"},
        {"id": 4, "name": "Rift Demon", "rarity": "Legendary", "hp": 15000, "atk": 2100, "def": 1250, "exp": (850, 1130), "coins": (1200, 2500), "drop": "Demon Core"},
        {"id": 5, "name": "Chaos Elemental", "rarity": "Legendary", "hp": 16000, "atk": 2200, "def": 1300, "exp": (860, 1140), "coins": (1200, 2500), "drop": "Chaos Crystal"},
        {"id": 6, "name": "Void Colossus", "rarity": "Legendary", "hp": 17000, "atk": 2300, "def": 1350, "exp": (870, 1150), "coins": (1200, 2500), "drop": "Colossus Core"},
        {"id": 7, "name": "Rift Titan", "rarity": "Legendary", "hp": 18000, "atk": 2400, "def": 1400, "exp": (880, 1160), "coins": (1200, 2500), "drop": "Titan Shard"},
        {"id": 8, "name": "Abyssal Wraith", "rarity": "Legendary", "hp": 19000, "atk": 2500, "def": 1450, "exp": (890, 1170), "coins": (1200, 2500), "drop": "Wraith Core"},
        {"id": 9, "name": "Void Emperor's Herald", "rarity": "Legendary", "hp": 20000, "atk": 2600, "def": 1500, "exp": (900, 1180), "coins": (1200, 2500), "drop": "Herald Crown"},
        {"id": 10, "name": "Rift Sovereign", "rarity": "Mythic", "hp": 25000, "atk": 3000, "def": 1800, "exp": (1000, 1400), "coins": (2500, 5000), "drop": "Sovereign Shard"},
    ]},
    10: {"name": "Cursed Marshlands", "level_range": (101, 125), "enemies": [
        {"id": 1, "name": "Bog Lurker", "rarity": "Rare", "hp": 28000, "atk": 3200, "def": 2000, "exp": (1050, 1500), "coins": (300, 600), "drop": "Bog Slime"},
        {"id": 2, "name": "Swamp Wraith", "rarity": "Rare", "hp": 30000, "atk": 3400, "def": 2100, "exp": (1100, 1550), "coins": (300, 600), "drop": "Wraith Mist"},
        {"id": 3, "name": "Marsh Serpent", "rarity": "Epic", "hp": 35000, "atk": 3800, "def": 2300, "exp": (1200, 1700), "coins": (600, 1200), "drop": "Serpent Venom"},
        {"id": 4, "name": "Cursed Toad King", "rarity": "Epic", "hp": 40000, "atk": 4000, "def": 2500, "exp": (1250, 1750), "coins": (600, 1200), "drop": "Toad Crown"},
        {"id": 5, "name": "Plague Bearer", "rarity": "Epic", "hp": 38000, "atk": 4200, "def": 2400, "exp": (1260, 1760), "coins": (600, 1200), "drop": "Plague Vial"},
        {"id": 6, "name": "Marsh Golem", "rarity": "Epic", "hp": 45000, "atk": 3600, "def": 3000, "exp": (1270, 1770), "coins": (600, 1200), "drop": "Marsh Stone"},
        {"id": 7, "name": "Venom Hydra", "rarity": "Legendary", "hp": 55000, "atk": 4500, "def": 3200, "exp": (1400, 1950), "coins": (1200, 2500), "drop": "Hydra Fang"},
        {"id": 8, "name": "Cursed Revenant", "rarity": "Legendary", "hp": 58000, "atk": 4700, "def": 3300, "exp": (1420, 1970), "coins": (1200, 2500), "drop": "Revenant Core"},
        {"id": 9, "name": "Swamp Colossus", "rarity": "Legendary", "hp": 62000, "atk": 4900, "def": 3500, "exp": (1440, 1990), "coins": (1200, 2500), "drop": "Colossus Mud"},
        {"id": 10, "name": "Marshland Demon", "rarity": "Legendary", "hp": 68000, "atk": 5200, "def": 3700, "exp": (1460, 2010), "coins": (1200, 2500), "drop": "Demon Marsh Core"},
    ]},
    11: {"name": "Abyssal Caverns", "level_range": (126, 150), "enemies": [
        {"id": 1, "name": "Cave Shadow", "rarity": "Epic", "hp": 75000, "atk": 5500, "def": 4000, "exp": (1500, 2100), "coins": (600, 1200), "drop": "Shadow Dust"},
        {"id": 2, "name": "Abyssal Bat", "rarity": "Epic", "hp": 72000, "atk": 5800, "def": 3800, "exp": (1520, 2120), "coins": (600, 1200), "drop": "Bat Wing"},
        {"id": 3, "name": "Crystal Golem", "rarity": "Epic", "hp": 85000, "atk": 5200, "def": 4500, "exp": (1540, 2140), "coins": (600, 1200), "drop": "Crystal Shard"},
        {"id": 4, "name": "Deep Stalker", "rarity": "Legendary", "hp": 95000, "atk": 6200, "def": 4800, "exp": (1650, 2300), "coins": (1200, 2500), "drop": "Stalker Claw"},
        {"id": 5, "name": "Cavern Wraith", "rarity": "Legendary", "hp": 100000, "atk": 6500, "def": 5000, "exp": (1670, 2320), "coins": (1200, 2500), "drop": "Wraith Dust"},
        {"id": 6, "name": "Abyssal Serpent", "rarity": "Legendary", "hp": 110000, "atk": 6800, "def": 5200, "exp": (1690, 2340), "coins": (1200, 2500), "drop": "Abyss Scale"},
        {"id": 7, "name": "Stone Colossus", "rarity": "Legendary", "hp": 120000, "atk": 7000, "def": 5500, "exp": (1710, 2360), "coins": (1200, 2500), "drop": "Stone Core"},
        {"id": 8, "name": "Deep Horror", "rarity": "Legendary", "hp": 130000, "atk": 7200, "def": 5700, "exp": (1730, 2380), "coins": (1200, 2500), "drop": "Horror Essence"},
        {"id": 9, "name": "Cavern Titan", "rarity": "Legendary", "hp": 140000, "atk": 7500, "def": 6000, "exp": (1750, 2400), "coins": (1200, 2500), "drop": "Titan Core"},
        {"id": 10, "name": "Abyssal Demon", "rarity": "Legendary", "hp": 150000, "atk": 7800, "def": 6200, "exp": (1770, 2420), "coins": (1200, 2500), "drop": "Demon Abyss Shard"},
        {"id": 11, "name": "Void Crawler", "rarity": "Mythic", "hp": 180000, "atk": 8500, "def": 7000, "exp": (2000, 2800), "coins": (2500, 5000), "drop": "Void Crawler Core"},
    ]},
    12: {"name": "Shattered Realm", "level_range": (151, 175), "enemies": [
        {"id": 1, "name": "Realm Shard", "rarity": "Epic", "hp": 200000, "atk": 9000, "def": 7500, "exp": (2100, 2900), "coins": (600, 1200), "drop": "Realm Fragment"},
        {"id": 2, "name": "Broken Knight", "rarity": "Epic", "hp": 210000, "atk": 9500, "def": 7800, "exp": (2120, 2920), "coins": (600, 1200), "drop": "Broken Armor"},
        {"id": 3, "name": "Shattered Golem", "rarity": "Legendary", "hp": 230000, "atk": 10000, "def": 8200, "exp": (2300, 3100), "coins": (1200, 2500), "drop": "Golem Shard"},
        {"id": 4, "name": "Realm Phantom", "rarity": "Legendary", "hp": 240000, "atk": 10500, "def": 8500, "exp": (2320, 3120), "coins": (1200, 2500), "drop": "Phantom Core"},
        {"id": 5, "name": "Fractured Titan", "rarity": "Legendary", "hp": 260000, "atk": 11000, "def": 9000, "exp": (2340, 3140), "coins": (1200, 2500), "drop": "Titan Fragment"},
        {"id": 6, "name": "Shard Demon", "rarity": "Legendary", "hp": 270000, "atk": 11500, "def": 9200, "exp": (2360, 3160), "coins": (1200, 2500), "drop": "Demon Shard"},
        {"id": 7, "name": "Realm Wraith", "rarity": "Legendary", "hp": 280000, "atk": 12000, "def": 9500, "exp": (2380, 3180), "coins": (1200, 2500), "drop": "Realm Wraith Dust"},
        {"id": 8, "name": "Broken God", "rarity": "Legendary", "hp": 300000, "atk": 12500, "def": 10000, "exp": (2400, 3200), "coins": (1200, 2500), "drop": "Broken Divine Shard"},
        {"id": 9, "name": "Shattered Colossus", "rarity": "Mythic", "hp": 350000, "atk": 14000, "def": 11000, "exp": (2800, 3800), "coins": (2500, 5000), "drop": "Colossus Myth Core"},
        {"id": 10, "name": "Realm Destroyer", "rarity": "Mythic", "hp": 380000, "atk": 15000, "def": 11500, "exp": (2850, 3850), "coins": (2500, 5000), "drop": "Destroyer Shard"},
        {"id": 11, "name": "Void Shard", "rarity": "Mythic", "hp": 400000, "atk": 16000, "def": 12000, "exp": (2900, 3900), "coins": (2500, 5000), "drop": "Pure Void Shard"},
        {"id": 12, "name": "Chaos Fragment", "rarity": "Mythic", "hp": 420000, "atk": 17000, "def": 12500, "exp": (2950, 3950), "coins": (2500, 5000), "drop": "Chaos Core"},
    ]},
    13: {"name": "The Nether", "level_range": (176, 200), "enemies": [
        {"id": 1, "name": "Nether Shade", "rarity": "Legendary", "hp": 450000, "atk": 18000, "def": 13000, "exp": (3000, 4000), "coins": (1200, 2500), "drop": "Nether Dust"},
        {"id": 2, "name": "Hell Hound", "rarity": "Legendary", "hp": 480000, "atk": 19000, "def": 13500, "exp": (3050, 4050), "coins": (1200, 2500), "drop": "Hell Fang"},
        {"id": 3, "name": "Nether Knight", "rarity": "Legendary", "hp": 500000, "atk": 20000, "def": 14000, "exp": (3100, 4100), "coins": (1200, 2500), "drop": "Nether Armor"},
        {"id": 4, "name": "Demon Stalker", "rarity": "Legendary", "hp": 520000, "atk": 21000, "def": 14500, "exp": (3150, 4150), "coins": (1200, 2500), "drop": "Stalker Demon Claw"},
        {"id": 5, "name": "Nether Wraith", "rarity": "Legendary", "hp": 540000, "atk": 22000, "def": 15000, "exp": (3200, 4200), "coins": (1200, 2500), "drop": "Nether Wraith Core"},
        {"id": 6, "name": "Infernal Golem", "rarity": "Legendary", "hp": 560000, "atk": 23000, "def": 15500, "exp": (3250, 4250), "coins": (1200, 2500), "drop": "Infernal Stone"},
        {"id": 7, "name": "Nether Titan", "rarity": "Mythic", "hp": 620000, "atk": 25000, "def": 17000, "exp": (3800, 5000), "coins": (2500, 5000), "drop": "Nether Titan Core"},
        {"id": 8, "name": "Hell Colossus", "rarity": "Mythic", "hp": 650000, "atk": 26000, "def": 17500, "exp": (3850, 5050), "coins": (2500, 5000), "drop": "Hell Colossus Shard"},
        {"id": 9, "name": "Nether Demon", "rarity": "Mythic", "hp": 680000, "atk": 27000, "def": 18000, "exp": (3900, 5100), "coins": (2500, 5000), "drop": "Nether Demon Core"},
        {"id": 10, "name": "Infernal Sovereign", "rarity": "Mythic", "hp": 720000, "atk": 28000, "def": 18500, "exp": (3950, 5150), "coins": (2500, 5000), "drop": "Infernal Crown"},
        {"id": 11, "name": "Nether God", "rarity": "Mythic", "hp": 760000, "atk": 29000, "def": 19000, "exp": (4000, 5200), "coins": (2500, 5000), "drop": "Nether God Shard"},
        {"id": 12, "name": "Hell Emperor", "rarity": "Mythic", "hp": 800000, "atk": 30000, "def": 19500, "exp": (4050, 5250), "coins": (2500, 5000), "drop": "Hell Emperor Crown"},
        {"id": 13, "name": "Nether Overlord", "rarity": "Mythic", "hp": 850000, "atk": 31000, "def": 20000, "exp": (4100, 5300), "coins": (2500, 5000), "drop": "Nether Overlord Core"},
    ]},
    14: {"name": "Demon's Domain", "level_range": (201, 230), "enemies": [
        {"id": 1, "name": "Domain Guard", "rarity": "Legendary", "hp": 900000, "atk": 32000, "def": 21000, "exp": (4200, 5500), "coins": (1200, 2500), "drop": "Guard Fragment"},
        {"id": 2, "name": "Demon Wraith", "rarity": "Legendary", "hp": 950000, "atk": 33000, "def": 21500, "exp": (4250, 5550), "coins": (1200, 2500), "drop": "Demon Wraith Dust"},
        {"id": 3, "name": "Shadow Demon", "rarity": "Legendary", "hp": 1000000, "atk": 34000, "def": 22000, "exp": (4300, 5600), "coins": (1200, 2500), "drop": "Shadow Demon Core"},
        {"id": 4, "name": "Domain Stalker", "rarity": "Mythic", "hp": 1100000, "atk": 36000, "def": 23000, "exp": (5000, 6500), "coins": (2500, 5000), "drop": "Domain Stalker Claw"},
        {"id": 5, "name": "Infernal Drake", "rarity": "Mythic", "hp": 1150000, "atk": 37000, "def": 23500, "exp": (5050, 6550), "coins": (2500, 5000), "drop": "Infernal Drake Scale"},
        {"id": 6, "name": "Demon Colossus", "rarity": "Mythic", "hp": 1200000, "atk": 38000, "def": 24000, "exp": (5100, 6600), "coins": (2500, 5000), "drop": "Demon Colossus Core"},
        {"id": 7, "name": "Domain Titan", "rarity": "Mythic", "hp": 1250000, "atk": 39000, "def": 24500, "exp": (5150, 6650), "coins": (2500, 5000), "drop": "Domain Titan Shard"},
        {"id": 8, "name": "Hell Guardian", "rarity": "Mythic", "hp": 1300000, "atk": 40000, "def": 25000, "exp": (5200, 6700), "coins": (2500, 5000), "drop": "Hell Guardian Core"},
        {"id": 9, "name": "Demon Sovereign", "rarity": "Mythic", "hp": 1350000, "atk": 41000, "def": 25500, "exp": (5250, 6750), "coins": (2500, 5000), "drop": "Demon Sovereign Crown"},
        {"id": 10, "name": "Domain Emperor", "rarity": "Mythic", "hp": 1400000, "atk": 42000, "def": 26000, "exp": (5300, 6800), "coins": (2500, 5000), "drop": "Domain Emperor Shard"},
        {"id": 11, "name": "Infernal Overlord", "rarity": "Mythic", "hp": 1450000, "atk": 43000, "def": 26500, "exp": (5350, 6850), "coins": (2500, 5000), "drop": "Infernal Overlord Core"},
        {"id": 12, "name": "Demon God", "rarity": "Mythic", "hp": 1500000, "atk": 44000, "def": 27000, "exp": (5400, 6900), "coins": (2500, 5000), "drop": "Demon God Shard"},
        {"id": 13, "name": "Domain Destroyer", "rarity": "Mythic", "hp": 1600000, "atk": 45000, "def": 28000, "exp": (5500, 7000), "coins": (2500, 5000), "drop": "Domain Destroyer Core"},
    ]},
    15: {"name": "Shadow Citadel", "level_range": (231, 270), "enemies": [
        {"id": 1, "name": "Citadel Guard", "rarity": "Legendary", "hp": 1700000, "atk": 46000, "def": 29000, "exp": (5600, 7100), "coins": (1200, 2500), "drop": "Citadel Guard Shard"},
        {"id": 2, "name": "Shadow Knight", "rarity": "Legendary", "hp": 1800000, "atk": 47000, "def": 30000, "exp": (5650, 7150), "coins": (1200, 2500), "drop": "Shadow Knight Armor"},
        {"id": 3, "name": "Dark Sentinel", "rarity": "Mythic", "hp": 1900000, "atk": 48000, "def": 31000, "exp": (6000, 7700), "coins": (2500, 5000), "drop": "Dark Sentinel Core"},
        {"id": 4, "name": "Citadel Wraith", "rarity": "Mythic", "hp": 2000000, "atk": 49000, "def": 32000, "exp": (6050, 7750), "coins": (2500, 5000), "drop": "Citadel Wraith Dust"},
        {"id": 5, "name": "Shadow Colossus", "rarity": "Mythic", "hp": 2100000, "atk": 50000, "def": 33000, "exp": (6100, 7800), "coins": (2500, 5000), "drop": "Shadow Colossus Core"},
        {"id": 6, "name": "Dark Titan", "rarity": "Mythic", "hp": 2200000, "atk": 51000, "def": 34000, "exp": (6150, 7850), "coins": (2500, 5000), "drop": "Dark Titan Shard"},
        {"id": 7, "name": "Citadel Demon", "rarity": "Mythic", "hp": 2300000, "atk": 52000, "def": 35000, "exp": (6200, 7900), "coins": (2500, 5000), "drop": "Citadel Demon Core"},
        {"id": 8, "name": "Shadow Sovereign", "rarity": "Mythic", "hp": 2400000, "atk": 53000, "def": 36000, "exp": (6250, 7950), "coins": (2500, 5000), "drop": "Shadow Sovereign Crown"},
        {"id": 9, "name": "Dark Emperor", "rarity": "Mythic", "hp": 2500000, "atk": 54000, "def": 37000, "exp": (6300, 8000), "coins": (2500, 5000), "drop": "Dark Emperor Shard"},
        {"id": 10, "name": "Citadel Destroyer", "rarity": "Mythic", "hp": 2600000, "atk": 55000, "def": 38000, "exp": (6350, 8050), "coins": (2500, 5000), "drop": "Citadel Destroyer Core"},
        {"id": 11, "name": "Shadow God", "rarity": "Mythic", "hp": 2700000, "atk": 56000, "def": 39000, "exp": (6400, 8100), "coins": (2500, 5000), "drop": "Shadow God Shard"},
        {"id": 12, "name": "Dark Overlord", "rarity": "Mythic", "hp": 2800000, "atk": 57000, "def": 40000, "exp": (6450, 8150), "coins": (2500, 5000), "drop": "Dark Overlord Core"},
        {"id": 13, "name": "Citadel Titan", "rarity": "Mythic", "hp": 2900000, "atk": 58000, "def": 41000, "exp": (6500, 8200), "coins": (2500, 5000), "drop": "Citadel Titan Core"},
        {"id": 14, "name": "Shadow Destroyer", "rarity": "Mythic", "hp": 3000000, "atk": 59000, "def": 42000, "exp": (6550, 8250), "coins": (2500, 5000), "drop": "Shadow Destroyer Shard"},
    ]},
    16: {"name": "Celestial Ruins", "level_range": (271, 310), "enemies": [
        {"id": 1, "name": "Ruined Angel", "rarity": "Mythic", "hp": 3200000, "atk": 61000, "def": 43000, "exp": (7000, 9000), "coins": (2500, 5000), "drop": "Ruined Angel Wing"},
        {"id": 2, "name": "Fallen Seraph", "rarity": "Mythic", "hp": 3400000, "atk": 63000, "def": 44000, "exp": (7050, 9050), "coins": (2500, 5000), "drop": "Fallen Seraph Core"},
        {"id": 3, "name": "Celestial Wraith", "rarity": "Mythic", "hp": 3600000, "atk": 65000, "def": 45000, "exp": (7100, 9100), "coins": (2500, 5000), "drop": "Celestial Wraith Dust"},
        {"id": 4, "name": "Ruined Titan", "rarity": "Mythic", "hp": 3800000, "atk": 67000, "def": 46000, "exp": (7150, 9150), "coins": (2500, 5000), "drop": "Ruined Titan Core"},
        {"id": 5, "name": "Fallen Colossus", "rarity": "Mythic", "hp": 4000000, "atk": 69000, "def": 47000, "exp": (7200, 9200), "coins": (2500, 5000), "drop": "Fallen Colossus Shard"},
        {"id": 6, "name": "Celestial Demon", "rarity": "Mythic", "hp": 4200000, "atk": 71000, "def": 48000, "exp": (7250, 9250), "coins": (2500, 5000), "drop": "Celestial Demon Core"},
        {"id": 7, "name": "Ruined God", "rarity": "Mythic", "hp": 4400000, "atk": 73000, "def": 49000, "exp": (7300, 9300), "coins": (2500, 5000), "drop": "Ruined God Shard"},
        {"id": 8, "name": "Fallen Emperor", "rarity": "Mythic", "hp": 4600000, "atk": 75000, "def": 50000, "exp": (7350, 9350), "coins": (2500, 5000), "drop": "Fallen Emperor Crown"},
        {"id": 9, "name": "Celestial Destroyer", "rarity": "Mythic", "hp": 4800000, "atk": 77000, "def": 51000, "exp": (7400, 9400), "coins": (2500, 5000), "drop": "Celestial Destroyer Core"},
        {"id": 10, "name": "Ruined Sovereign", "rarity": "Mythic", "hp": 5000000, "atk": 79000, "def": 52000, "exp": (7450, 9450), "coins": (2500, 5000), "drop": "Ruined Sovereign Crown"},
        {"id": 11, "name": "Fallen Overlord", "rarity": "Mythic", "hp": 5200000, "atk": 81000, "def": 53000, "exp": (7500, 9500), "coins": (2500, 5000), "drop": "Fallen Overlord Core"},
        {"id": 12, "name": "Celestial Titan", "rarity": "Mythic", "hp": 5400000, "atk": 83000, "def": 54000, "exp": (7550, 9550), "coins": (2500, 5000), "drop": "Celestial Titan Shard"},
        {"id": 13, "name": "Ruined Destroyer", "rarity": "Mythic", "hp": 5600000, "atk": 85000, "def": 55000, "exp": (7600, 9600), "coins": (2500, 5000), "drop": "Ruined Destroyer Core"},
        {"id": 14, "name": "Fallen God", "rarity": "Mythic", "hp": 5800000, "atk": 87000, "def": 56000, "exp": (7650, 9650), "coins": (2500, 5000), "drop": "Fallen God Shard"},
        {"id": 15, "name": "Celestial Sovereign", "rarity": "Divine", "hp": 6500000, "atk": 95000, "def": 62000, "exp": (9000, 11500), "coins": (5000, 10000), "drop": "Celestial Sovereign Crown"},
    ]},
    17: {"name": "The Dark Throne", "level_range": (311, 350), "enemies": [
        {"id": 1, "name": "Throne Guard", "rarity": "Mythic", "hp": 7000000, "atk": 100000, "def": 65000, "exp": (9500, 12000), "coins": (2500, 5000), "drop": "Throne Guard Shard"},
        {"id": 2, "name": "Dark Herald", "rarity": "Mythic", "hp": 7500000, "atk": 105000, "def": 68000, "exp": (9550, 12050), "coins": (2500, 5000), "drop": "Dark Herald Core"},
        {"id": 3, "name": "Throne Wraith", "rarity": "Mythic", "hp": 8000000, "atk": 110000, "def": 71000, "exp": (9600, 12100), "coins": (2500, 5000), "drop": "Throne Wraith Dust"},
        {"id": 4, "name": "Dark Sentinel", "rarity": "Mythic", "hp": 8500000, "atk": 115000, "def": 74000, "exp": (9650, 12150), "coins": (2500, 5000), "drop": "Dark Sentinel Core"},
        {"id": 5, "name": "Throne Colossus", "rarity": "Mythic", "hp": 9000000, "atk": 120000, "def": 77000, "exp": (9700, 12200), "coins": (2500, 5000), "drop": "Throne Colossus Shard"},
        {"id": 6, "name": "Dark Titan", "rarity": "Mythic", "hp": 9500000, "atk": 125000, "def": 80000, "exp": (9750, 12250), "coins": (2500, 5000), "drop": "Dark Titan Core"},
        {"id": 7, "name": "Throne Demon", "rarity": "Divine", "hp": 11000000, "atk": 140000, "def": 90000, "exp": (11000, 14000), "coins": (5000, 10000), "drop": "Throne Demon Core"},
        {"id": 8, "name": "Dark Sovereign", "rarity": "Divine", "hp": 11500000, "atk": 145000, "def": 93000, "exp": (11100, 14100), "coins": (5000, 10000), "drop": "Dark Sovereign Crown"},
        {"id": 9, "name": "Throne Emperor", "rarity": "Divine", "hp": 12000000, "atk": 150000, "def": 96000, "exp": (11200, 14200), "coins": (5000, 10000), "drop": "Throne Emperor Shard"},
        {"id": 10, "name": "Dark Destroyer", "rarity": "Divine", "hp": 12500000, "atk": 155000, "def": 99000, "exp": (11300, 14300), "coins": (5000, 10000), "drop": "Dark Destroyer Core"},
        {"id": 11, "name": "Throne God", "rarity": "Divine", "hp": 13000000, "atk": 160000, "def": 102000, "exp": (11400, 14400), "coins": (5000, 10000), "drop": "Throne God Shard"},
        {"id": 12, "name": "Dark Overlord", "rarity": "Divine", "hp": 13500000, "atk": 165000, "def": 105000, "exp": (11500, 14500), "coins": (5000, 10000), "drop": "Dark Overlord Core"},
        {"id": 13, "name": "Throne Titan", "rarity": "Divine", "hp": 14000000, "atk": 170000, "def": 108000, "exp": (11600, 14600), "coins": (5000, 10000), "drop": "Throne Titan Core"},
        {"id": 14, "name": "Dark God", "rarity": "Divine", "hp": 14500000, "atk": 175000, "def": 111000, "exp": (11700, 14700), "coins": (5000, 10000), "drop": "Dark God Shard"},
        {"id": 15, "name": "Throne Sovereign", "rarity": "Divine", "hp": 15000000, "atk": 180000, "def": 114000, "exp": (11800, 14800), "coins": (5000, 10000), "drop": "Throne Sovereign Crown"},
        {"id": 16, "name": "Dark Emperor", "rarity": "Divine", "hp": 16000000, "atk": 190000, "def": 120000, "exp": (12000, 15000), "coins": (5000, 10000), "drop": "Dark Emperor Core"},
    ]},
    18: {"name": "Primordial Abyss", "level_range": (351, 400), "enemies": [
        {"id": 1, "name": "Abyss Warden", "rarity": "Mythic", "hp": 18000000, "atk": 210000, "def": 135000, "exp": (13000, 16500), "coins": (2500, 5000), "drop": "Abyss Warden Core"},
        {"id": 2, "name": "Primordial Shade", "rarity": "Mythic", "hp": 19000000, "atk": 220000, "def": 140000, "exp": (13100, 16600), "coins": (2500, 5000), "drop": "Primordial Shade Dust"},
        {"id": 3, "name": "Ancient Crawler", "rarity": "Mythic", "hp": 20000000, "atk": 230000, "def": 145000, "exp": (13200, 16700), "coins": (2500, 5000), "drop": "Ancient Crawler Core"},
        {"id": 4, "name": "Abyss Titan", "rarity": "Divine", "hp": 22000000, "atk": 250000, "def": 155000, "exp": (15000, 19000), "coins": (5000, 10000), "drop": "Abyss Titan Shard"},
        {"id": 5, "name": "Primordial Wraith", "rarity": "Divine", "hp": 23000000, "atk": 260000, "def": 160000, "exp": (15100, 19100), "coins": (5000, 10000), "drop": "Primordial Wraith Dust"},
        {"id": 6, "name": "Ancient Demon", "rarity": "Divine", "hp": 24000000, "atk": 270000, "def": 165000, "exp": (15200, 19200), "coins": (5000, 10000), "drop": "Ancient Demon Core"},
        {"id": 7, "name": "Abyss Sovereign", "rarity": "Divine", "hp": 25000000, "atk": 280000, "def": 170000, "exp": (15300, 19300), "coins": (5000, 10000), "drop": "Abyss Sovereign Crown"},
        {"id": 8, "name": "Primordial Colossus", "rarity": "Divine", "hp": 26000000, "atk": 290000, "def": 175000, "exp": (15400, 19400), "coins": (5000, 10000), "drop": "Primordial Colossus Core"},
        {"id": 9, "name": "Ancient God", "rarity": "Divine", "hp": 27000000, "atk": 300000, "def": 180000, "exp": (15500, 19500), "coins": (5000, 10000), "drop": "Ancient God Shard"},
        {"id": 10, "name": "Abyss Emperor", "rarity": "Divine", "hp": 28000000, "atk": 310000, "def": 185000, "exp": (15600, 19600), "coins": (5000, 10000), "drop": "Abyss Emperor Crown"},
        {"id": 11, "name": "Primordial Destroyer", "rarity": "Divine", "hp": 29000000, "atk": 320000, "def": 190000, "exp": (15700, 19700), "coins": (5000, 10000), "drop": "Primordial Destroyer Core"},
        {"id": 12, "name": "Ancient Overlord", "rarity": "Divine", "hp": 30000000, "atk": 330000, "def": 195000, "exp": (15800, 19800), "coins": (5000, 10000), "drop": "Ancient Overlord Shard"},
        {"id": 13, "name": "Abyss God", "rarity": "Divine", "hp": 31000000, "atk": 340000, "def": 200000, "exp": (15900, 19900), "coins": (5000, 10000), "drop": "Abyss God Core"},
        {"id": 14, "name": "Primordial Sovereign", "rarity": "Divine", "hp": 32000000, "atk": 350000, "def": 205000, "exp": (16000, 20000), "coins": (5000, 10000), "drop": "Primordial Sovereign Crown"},
        {"id": 15, "name": "Ancient Emperor", "rarity": "Divine", "hp": 33000000, "atk": 360000, "def": 210000, "exp": (16100, 20100), "coins": (5000, 10000), "drop": "Ancient Emperor Core"},
        {"id": 16, "name": "Abyss Overlord", "rarity": "Divine", "hp": 34000000, "atk": 370000, "def": 215000, "exp": (16200, 20200), "coins": (5000, 10000), "drop": "Abyss Overlord Shard"},
        {"id": 17, "name": "Primordial God", "rarity": "Divine", "hp": 35000000, "atk": 380000, "def": 220000, "exp": (16300, 20300), "coins": (5000, 10000), "drop": "Primordial God Core"},
        {"id": 18, "name": "Ancient Destroyer", "rarity": "Divine", "hp": 36000000, "atk": 390000, "def": 225000, "exp": (16400, 20400), "coins": (5000, 10000), "drop": "Ancient Destroyer Shard"},
    ]},
    19: {"name": "The God Realm", "level_range": (401, 450), "enemies": [
        {"id": 1, "name": "Realm Warden", "rarity": "Divine", "hp": 40000000, "atk": 420000, "def": 245000, "exp": (17000, 21500), "coins": (5000, 10000), "drop": "Realm Warden Core"},
        {"id": 2, "name": "God's Herald", "rarity": "Divine", "hp": 42000000, "atk": 440000, "def": 255000, "exp": (17100, 21600), "coins": (5000, 10000), "drop": "God Herald Shard"},
        {"id": 3, "name": "Celestial Warden", "rarity": "Divine", "hp": 44000000, "atk": 460000, "def": 265000, "exp": (17200, 21700), "coins": (5000, 10000), "drop": "Celestial Warden Core"},
        {"id": 4, "name": "Realm Titan", "rarity": "Divine", "hp": 46000000, "atk": 480000, "def": 275000, "exp": (17300, 21800), "coins": (5000, 10000), "drop": "Realm Titan Shard"},
        {"id": 5, "name": "God's Sentinel", "rarity": "Divine", "hp": 48000000, "atk": 500000, "def": 285000, "exp": (17400, 21900), "coins": (5000, 10000), "drop": "God Sentinel Core"},
        {"id": 6, "name": "Celestial Sovereign", "rarity": "Divine", "hp": 50000000, "atk": 520000, "def": 295000, "exp": (17500, 22000), "coins": (5000, 10000), "drop": "Celestial Sovereign Crown"},
        {"id": 7, "name": "Realm Destroyer", "rarity": "Divine", "hp": 52000000, "atk": 540000, "def": 305000, "exp": (17600, 22100), "coins": (5000, 10000), "drop": "Realm Destroyer Core"},
        {"id": 8, "name": "God's Colossus", "rarity": "Divine", "hp": 54000000, "atk": 560000, "def": 315000, "exp": (17700, 22200), "coins": (5000, 10000), "drop": "God Colossus Shard"},
        {"id": 9, "name": "Celestial Emperor", "rarity": "Divine", "hp": 56000000, "atk": 580000, "def": 325000, "exp": (17800, 22300), "coins": (5000, 10000), "drop": "Celestial Emperor Crown"},
        {"id": 10, "name": "Realm Sovereign", "rarity": "Divine", "hp": 58000000, "atk": 600000, "def": 335000, "exp": (17900, 22400), "coins": (5000, 10000), "drop": "Realm Sovereign Core"},
        {"id": 11, "name": "God's Destroyer", "rarity": "Divine", "hp": 60000000, "atk": 620000, "def": 345000, "exp": (18000, 22500), "coins": (5000, 10000), "drop": "God Destroyer Shard"},
        {"id": 12, "name": "Celestial Overlord", "rarity": "Divine", "hp": 62000000, "atk": 640000, "def": 355000, "exp": (18100, 22600), "coins": (5000, 10000), "drop": "Celestial Overlord Core"},
        {"id": 13, "name": "Realm Emperor", "rarity": "Divine", "hp": 64000000, "atk": 660000, "def": 365000, "exp": (18200, 22700), "coins": (5000, 10000), "drop": "Realm Emperor Crown"},
        {"id": 14, "name": "God's Overlord", "rarity": "Divine", "hp": 66000000, "atk": 680000, "def": 375000, "exp": (18300, 22800), "coins": (5000, 10000), "drop": "God Overlord Shard"},
        {"id": 15, "name": "Celestial God", "rarity": "Divine", "hp": 68000000, "atk": 700000, "def": 385000, "exp": (18400, 22900), "coins": (5000, 10000), "drop": "Celestial God Core"},
        {"id": 16, "name": "Realm God", "rarity": "Divine", "hp": 70000000, "atk": 720000, "def": 395000, "exp": (18500, 23000), "coins": (5000, 10000), "drop": "Realm God Shard"},
        {"id": 17, "name": "God's Emperor", "rarity": "Divine", "hp": 72000000, "atk": 740000, "def": 405000, "exp": (18600, 23100), "coins": (5000, 10000), "drop": "God Emperor Crown"},
        {"id": 18, "name": "Celestial Destroyer", "rarity": "Divine", "hp": 74000000, "atk": 760000, "def": 415000, "exp": (18700, 23200), "coins": (5000, 10000), "drop": "Celestial Destroyer Core"},
        {"id": 19, "name": "Realm Overlord", "rarity": "Divine", "hp": 76000000, "atk": 780000, "def": 425000, "exp": (18800, 23300), "coins": (5000, 10000), "drop": "Realm Overlord Shard"},
        {"id": 20, "name": "God's Sovereign", "rarity": "Divine", "hp": 80000000, "atk": 800000, "def": 440000, "exp": (19000, 23500), "coins": (5000, 10000), "drop": "God Sovereign Crown"},
    ]},
    20: {"name": "Edge of Existence", "level_range": (451, 500), "enemies": [
        {"id": 1, "name": "Existence Warden", "rarity": "Divine", "hp": 85000000, "atk": 850000, "def": 470000, "exp": (20000, 25000), "coins": (5000, 10000), "drop": "Existence Warden Core"},
        {"id": 2, "name": "Edge Sentinel", "rarity": "Divine", "hp": 88000000, "atk": 880000, "def": 485000, "exp": (20100, 25100), "coins": (5000, 10000), "drop": "Edge Sentinel Shard"},
        {"id": 3, "name": "Void Existence", "rarity": "Divine", "hp": 91000000, "atk": 910000, "def": 500000, "exp": (20200, 25200), "coins": (5000, 10000), "drop": "Void Existence Core"},
        {"id": 4, "name": "Edge Titan", "rarity": "Divine", "hp": 94000000, "atk": 940000, "def": 515000, "exp": (20300, 25300), "coins": (5000, 10000), "drop": "Edge Titan Shard"},
        {"id": 5, "name": "Existence Sovereign", "rarity": "Divine", "hp": 97000000, "atk": 970000, "def": 530000, "exp": (20400, 25400), "coins": (5000, 10000), "drop": "Existence Sovereign Crown"},
        {"id": 6, "name": "Edge Colossus", "rarity": "Divine", "hp": 100000000, "atk": 1000000, "def": 545000, "exp": (20500, 25500), "coins": (5000, 10000), "drop": "Edge Colossus Core"},
        {"id": 7, "name": "Void Edge", "rarity": "Divine", "hp": 103000000, "atk": 1030000, "def": 560000, "exp": (20600, 25600), "coins": (5000, 10000), "drop": "Void Edge Shard"},
        {"id": 8, "name": "Existence Emperor", "rarity": "Divine", "hp": 106000000, "atk": 1060000, "def": 575000, "exp": (20700, 25700), "coins": (5000, 10000), "drop": "Existence Emperor Crown"},
        {"id": 9, "name": "Edge Destroyer", "rarity": "Divine", "hp": 109000000, "atk": 1090000, "def": 590000, "exp": (20800, 25800), "coins": (5000, 10000), "drop": "Edge Destroyer Core"},
        {"id": 10, "name": "Void Sovereign", "rarity": "Divine", "hp": 112000000, "atk": 1120000, "def": 605000, "exp": (20900, 25900), "coins": (5000, 10000), "drop": "Void Sovereign Crown"},
        {"id": 11, "name": "Existence Overlord", "rarity": "Divine", "hp": 115000000, "atk": 1150000, "def": 620000, "exp": (21000, 26000), "coins": (5000, 10000), "drop": "Existence Overlord Shard"},
        {"id": 12, "name": "Edge God", "rarity": "Divine", "hp": 118000000, "atk": 1180000, "def": 635000, "exp": (21100, 26100), "coins": (5000, 10000), "drop": "Edge God Core"},
        {"id": 13, "name": "Void Emperor", "rarity": "Divine", "hp": 121000000, "atk": 1210000, "def": 650000, "exp": (21200, 26200), "coins": (5000, 10000), "drop": "Void Emperor Crown"},
        {"id": 14, "name": "Existence God", "rarity": "Divine", "hp": 124000000, "atk": 1240000, "def": 665000, "exp": (21300, 26300), "coins": (5000, 10000), "drop": "Existence God Shard"},
        {"id": 15, "name": "Edge Overlord", "rarity": "Divine", "hp": 127000000, "atk": 1270000, "def": 680000, "exp": (21400, 26400), "coins": (5000, 10000), "drop": "Edge Overlord Core"},
        {"id": 16, "name": "Void God", "rarity": "Divine", "hp": 130000000, "atk": 1300000, "def": 695000, "exp": (21500, 26500), "coins": (5000, 10000), "drop": "Void God Shard"},
        {"id": 17, "name": "Existence Destroyer", "rarity": "Divine", "hp": 133000000, "atk": 1330000, "def": 710000, "exp": (21600, 26600), "coins": (5000, 10000), "drop": "Existence Destroyer Core"},
        {"id": 18, "name": "Edge Emperor", "rarity": "Divine", "hp": 136000000, "atk": 1360000, "def": 725000, "exp": (21700, 26700), "coins": (5000, 10000), "drop": "Edge Emperor Crown"},
        {"id": 19, "name": "Void Overlord", "rarity": "Divine", "hp": 139000000, "atk": 1390000, "def": 740000, "exp": (21800, 26800), "coins": (5000, 10000), "drop": "Void Overlord Shard"},
        {"id": 20, "name": "Existence Titan", "rarity": "Divine", "hp": 142000000, "atk": 1420000, "def": 755000, "exp": (21900, 26900), "coins": (5000, 10000), "drop": "Existence Titan Core"},
        {"id": 21, "name": "Edge Sovereign", "rarity": "Divine", "hp": 145000000, "atk": 1450000, "def": 770000, "exp": (22000, 27000), "coins": (5000, 10000), "drop": "Edge Sovereign Crown"},
        {"id": 22, "name": "Void Destroyer", "rarity": "Divine", "hp": 148000000, "atk": 1480000, "def": 785000, "exp": (22100, 27100), "coins": (5000, 10000), "drop": "Void Destroyer Core"},
        {"id": 23, "name": "Existence Sentinel", "rarity": "Divine", "hp": 151000000, "atk": 1510000, "def": 800000, "exp": (22200, 27200), "coins": (5000, 10000), "drop": "Existence Sentinel Shard"},
        {"id": 24, "name": "Edge Warden", "rarity": "Divine", "hp": 154000000, "atk": 1540000, "def": 815000, "exp": (22300, 27300), "coins": (5000, 10000), "drop": "Edge Warden Core"},
        {"id": 25, "name": "The Final Existence", "rarity": "Transcendent", "hp": 200000000, "atk": 2000000, "def": 1000000, "exp": (25000, 30000), "coins": (10000, 25000), "drop": "Fragment of Existence"},
    ]},
}

# ─── HELPER FUNCTIONS ───
def format_number(n):
    try:
        n = float(n)
    except (TypeError, ValueError):
        return str(n)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n < 1000:
        return f"{sign}{int(n) if n == int(n) else n:,}"
    units = [
        (1e33, "D"), (1e30, "N"), (1e27, "O"), (1e24, "Sp"), (1e21, "Sx"),
        (1e18, "Qi"), (1e15, "Qa"), (1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K"),
    ]
    for value, suffix in units:
        if n >= value:
            result = n / value
            if result >= 1000:
                continue
            formatted = f"{result:.2f}".rstrip('0').rstrip('.')
            return f"{sign}{formatted}{suffix}"
    return f"{sign}{n:.2e}"

def exp_required(level):
    return int(100 * (1.5 ** (level - 1)))

def get_skill_effect(race, skill_index, level):
    skill = RACE_SKILLS[race]["skills"][skill_index]
    effects = skill.get("effects")
    if not effects:
        return None
    for i in range(len(skill["evo_levels"]) - 1, -1, -1):
        if level >= skill["evo_levels"][i]:
            return effects[i] if i < len(effects) else effects[-1]
    return effects[0]

def get_special_effect(race):
    return RACE_SKILLS[race]["special"].get("effect")

def get_skill_name(race, skill_index, level):
    skill = RACE_SKILLS[race]["skills"][skill_index]
    for i in range(len(skill["evo_levels"]) - 1, -1, -1):
        if level >= skill["evo_levels"][i]:
            return skill["evolutions"][i]
    return skill["evolutions"][0]

def get_points_for_level(level):
    if level <= 100:
        return 15
    elif level <= 250:
        return 25
    elif level <= 500:
        return 40
    elif level <= 750:
        return 58
    else:
        return 88

def get_stat_increase(level):
    if level <= 100:
        return {"hp": 5, "str": 2, "mag": 2, "def": 2}
    elif level <= 250:
        return {"hp": 8, "str": 3, "mag": 3, "def": 3}
    elif level <= 500:
        return {"hp": 12, "str": 5, "mag": 5, "def": 5}
    elif level <= 750:
        return {"hp": 18, "str": 8, "mag": 8, "def": 8}
    else:
        return {"hp": 25, "str": 12, "mag": 12, "def": 12}

def check_ban(user_id):
    p = players.search(Player.id == str(user_id))
    if not p:
        return False
    p = p[0]
    if not p.get('banned', False):
        return False
    expiry = p.get('ban_expiry')
    if expiry and time.time() > expiry:
        players.update({'banned': False, 'ban_expiry': None}, Player.id == str(user_id))
        return False
    return True

def get_prefix(bot, message):
    user_id = str(message.author.id)
    result = prefixes_table.search(Prefix.id == user_id)
    if result:
        return result[0]['prefix']
    return '!'

def is_admin(user_id):
    return str(user_id) in ADMIN_IDS

# ─── BOT SETUP ───
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)

# ─── ADMIN COMMANDS (in main.py to guarantee they load) ───
@bot.command(name="adminhelp")
async def adminhelp(ctx):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    embed = discord.Embed(title="🛡️ Admin Commands", color=GOLD)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    embed.add_field(name="👤 Player",
        value="`!setrace @user <race>`\n`!setorigin @user <origin>`\n`!setlevel @user <level>`\n`!setexp @user <amount>`\n`!resetplayer @user`\n`!giveitem @user <rarity> <name>`",
        inline=False)
    embed.add_field(name="💰 Economy",
        value="`!addcoins @user <amount>`\n`!removecoins @user <amount>`\n`!addstarshards @user <amount>`\n`!removestarshards @user <amount>`",
        inline=False)
    embed.add_field(name="🚫 Moderation",
        value="`!ban @user`\n`!unban @user`\n`!tempban @user <duration>`",
        inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    embed.set_footer(text="Nexworld RPG • Admin Panel")
    await ctx.send(embed=embed)

@bot.command(name="setrace")
async def setrace(ctx, member: discord.Member = None, *, new_race: str = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or not new_race:
        await ctx.send(embed=discord.Embed(description="Usage: `!setrace @user <race>`", color=GOLD))
        return
    actual_race = next((r for r in RACES if r.lower() == new_race.lower()), None)
    if not actual_race:
        await ctx.send(embed=discord.Embed(description=f"❌ Invalid race! Valid: {', '.join(RACES.keys())}", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    stats = RACES[actual_race]
    players.update({'race': actual_race, 'hp': stats['hp'], 'str': stats['str'], 'mag': stats['mag'], 'def': stats['def']}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Race Updated", description=f"{member.mention} → **{actual_race}**!", color=GOLD))

@bot.command(name="setorigin")
async def setorigin(ctx, member: discord.Member = None, *, new_origin: str = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or not new_origin:
        await ctx.send(embed=discord.Embed(description="Usage: `!setorigin @user <origin>`", color=GOLD))
        return
    actual_origin = next((o for o in ORIGINS if o.lower() == new_origin.lower()), None)
    if not actual_origin:
        await ctx.send(embed=discord.Embed(description="❌ Invalid! Valid: Normal, Reincarnation, Teleported", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    players.update({'origin': actual_origin}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Origin Updated", description=f"{member.mention} → **{actual_origin}**!", color=GOLD))

@bot.command(name="setlevel")
async def setlevel(ctx, member: discord.Member = None, level: int = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or level is None:
        await ctx.send(embed=discord.Embed(description="Usage: `!setlevel @user <level>`", color=GOLD))
        return
    if level < 1 or level > 1000:
        await ctx.send(embed=discord.Embed(description="❌ Level must be 1-1000!", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    p = players.search(Player.id == user_id)[0]
    old_level = p.get('level', 1)
    points_gained = 0
    if level > old_level:
        for lv in range(old_level + 1, level + 1):
            points_gained += get_points_for_level(lv)
    current_unspent = p.get('unspent_points', 0) + points_gained
    players.update({'level': level, 'exp': 0, 'unspent_points': current_unspent}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Level Updated", description=f"{member.mention} → Level **{level}**!\nGiven `{points_gained}` unspent points for the level gain.", color=GOLD))

@bot.command(name="setexp")
async def setexp(ctx, member: discord.Member = None, amount: int = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or amount is None:
        await ctx.send(embed=discord.Embed(description="Usage: `!setexp @user <amount>`", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    players.update({'exp': amount}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ EXP Updated", description=f"{member.mention} → **{amount:,}** EXP!", color=GOLD))

@bot.command(name="addcoins")
async def addcoins(ctx, member: discord.Member = None, amount: int = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or amount is None:
        await ctx.send(embed=discord.Embed(description="Usage: `!addcoins @user <amount>`", color=GOLD))
        return
    user_id = str(member.id)
    p = players.search(Player.id == user_id)
    if not p:
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    new_coins = p[0].get('nexcoins', 0) + amount
    players.update({'nexcoins': new_coins}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Nexcoins Added", description=f"Added **{amount:,}** to {member.mention}!\nBalance: `{new_coins:,}`", color=GOLD))

@bot.command(name="removecoins")
async def removecoins(ctx, member: discord.Member = None, amount: int = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or amount is None:
        await ctx.send(embed=discord.Embed(description="Usage: `!removecoins @user <amount>`", color=GOLD))
        return
    user_id = str(member.id)
    p = players.search(Player.id == user_id)
    if not p:
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    new_coins = max(0, p[0].get('nexcoins', 0) - amount)
    players.update({'nexcoins': new_coins}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Nexcoins Removed", description=f"Removed **{amount:,}** from {member.mention}!\nBalance: `{new_coins:,}`", color=GOLD))

@bot.command(name="addstarshards")
async def addstarshards(ctx, member: discord.Member = None, amount: int = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or amount is None:
        await ctx.send(embed=discord.Embed(description="Usage: `!addstarshards @user <amount>`", color=GOLD))
        return
    user_id = str(member.id)
    p = players.search(Player.id == user_id)
    if not p:
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    new_ss = p[0].get('starshards', 0) + amount
    players.update({'starshards': new_ss}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Starshards Added", description=f"Added **{amount}** to {member.mention}!\nBalance: `{new_ss}`", color=GOLD))

@bot.command(name="removestarshards")
async def removestarshards(ctx, member: discord.Member = None, amount: int = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or amount is None:
        await ctx.send(embed=discord.Embed(description="Usage: `!removestarshards @user <amount>`", color=GOLD))
        return
    user_id = str(member.id)
    p = players.search(Player.id == user_id)
    if not p:
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    new_ss = max(0, p[0].get('starshards', 0) - amount)
    players.update({'starshards': new_ss}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Starshards Removed", description=f"Removed **{amount}** from {member.mention}!\nBalance: `{new_ss}`", color=GOLD))

@bot.command(name="giveitem")
async def giveitem(ctx, member: discord.Member = None, rarity: str = None, *, item_name: str = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or not rarity or not item_name:
        await ctx.send(embed=discord.Embed(description="Usage: `!giveitem @user <rarity> <item name>`", color=GOLD))
        return
    user_id = str(member.id)
    p = players.search(Player.id == user_id)
    if not p:
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    inv = p[0].get('inventory', [])
    admin_items = [i for i in inv if i['uid'].startswith('A')]
    uid = f"A{str(len(admin_items) + 1).zfill(3)}"
    inv.append({'uid': uid, 'name': item_name, 'rarity': rarity, 'type': 'admin_given'})
    players.update({'inventory': inv}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Item Given", description=f"Gave **{item_name}** (`{rarity}`) to {member.mention}!\nID: `{uid}`", color=GOLD))

@bot.command(name="resetplayer")
async def resetplayer(ctx, member: discord.Member = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member:
        await ctx.send(embed=discord.Embed(description="Usage: `!resetplayer @user`", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    players.remove(Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Player Reset", description=f"{member.mention}'s data wiped!", color=GOLD))

@bot.command(name="ban")
async def ban(ctx, member: discord.Member = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member:
        await ctx.send(embed=discord.Embed(description="Usage: `!ban @user`", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    players.update({'banned': True, 'ban_expiry': None}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="🚫 Banned", description=f"{member.mention} banned!", color=GOLD))

@bot.command(name="unban")
async def unban(ctx, member: discord.Member = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member:
        await ctx.send(embed=discord.Embed(description="Usage: `!unban @user`", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    players.update({'banned': False, 'ban_expiry': None}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="✅ Unbanned", description=f"{member.mention} unbanned!", color=GOLD))

@bot.command(name="tempban")
async def tempban(ctx, member: discord.Member = None, duration: str = None):
    if not is_admin(ctx.author.id):
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return
    if not member or not duration:
        await ctx.send(embed=discord.Embed(description="Usage: `!tempban @user <duration>` (24h, 7d, 30m)", color=GOLD))
        return
    user_id = str(member.id)
    if not players.search(Player.id == user_id):
        await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
        return
    try:
        if duration.endswith('h'):
            seconds = int(duration[:-1]) * 3600
        elif duration.endswith('d'):
            seconds = int(duration[:-1]) * 86400
        elif duration.endswith('m'):
            seconds = int(duration[:-1]) * 60
        else:
            raise ValueError
    except ValueError:
        await ctx.send(embed=discord.Embed(description="❌ Invalid! Use: 24h, 7d, 30m", color=GOLD))
        return
    players.update({'banned': True, 'ban_expiry': time.time() + seconds}, Player.id == user_id)
    await ctx.send(embed=discord.Embed(title="⏰ Temp Banned", description=f"{member.mention} banned for **{duration}**!", color=GOLD))

@bot.command(name="ping")
async def ping(ctx):
    await ctx.send(embed=discord.Embed(description="⚡ Nexworld is alive!", color=GOLD))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(embed=discord.Embed(description=f"❌ Missing argument: `{error.param.name}`", color=GOLD))
    elif isinstance(error, commands.BadArgument):
        await ctx.send(embed=discord.Embed(description=f"❌ Invalid argument: {str(error)}", color=GOLD))
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send(embed=discord.Embed(description=f"❌ Member not found: {str(error)}", color=GOLD))
    else:
        import traceback
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        tb_str = ''.join(tb)
        print(f"Error in {ctx.command}:\n{tb_str}")
        await ctx.send(embed=discord.Embed(
            title="❌ Command Error",
            description=f"Something went wrong in `!{ctx.command}`:\n```{str(error)[:500]}```",
            color=0xFF0000))

@bot.event
async def on_ready():
    print(f"Nexworld is online! Logged in as {bot.user}")
    await bot.change_presence(activity=discord.Game(name="⚔️ Nexworld RPG"))

async def load_cogs():
    await bot.load_extension('cogs.profile')
    await bot.load_extension('cogs.battle')
    await bot.load_extension('cogs.shop')
    await bot.load_extension('cogs.economy')
    await bot.load_extension('cogs.raid')
    await bot.load_extension('cogs.guild')
    await bot.load_extension('cogs.clan')
    await bot.load_extension('cogs.trade')

async def main():
    async with bot:
        await load_cogs()
        await bot.start(os.getenv("DISCORD_TOKEN"))

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        import traceback
        print(f"BOT CRASHED: {e}")
        traceback.print_exc()