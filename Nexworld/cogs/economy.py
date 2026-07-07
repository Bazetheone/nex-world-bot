import discord
from discord.ext import commands
from tinydb import Query
from db import players, market_table, prefixes_table, Player
import random
import time
import os

_COGS_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(os.path.dirname(_COGS_DIR), 'static')

EXPLORE_ZONES = [
    {"name": "🌌 Celestial Spire of Aeloria", "img": "explore_sky.png",  "flavor": "You ascended through the clouds and discovered a magnificent ancient spire!"},
    {"name": "🔥 Infernal Forge of Ashveil",  "img": "explore_lava.png", "flavor": "You ventured into the scorching depths and found a roaring forge of molten steel!"},
]

Market = Query()

GOLD = 0xFFD700
ALLOWED_PREFIXES = ['!', '$', '-', '*', '?', '.']

ORIGINS = ["Normal", "Reincarnation", "Teleported"]
ORIGIN_WEIGHTS = [65, 25, 10]

RACES = {
    "Human":     {"rarity": "Common",    "rarity_icon": "⭐", "hp": 100, "str": 10, "mag": 10, "def": 10},
    "Halfblood": {"rarity": "Common",    "rarity_icon": "⭐", "hp": 100, "str": 10, "mag": 14, "def": 11},
    "Kobold":    {"rarity": "Common",    "rarity_icon": "⭐", "hp": 100, "str": 10, "mag": 8,  "def": 11},
    "Elf":       {"rarity": "Rare",      "rarity_icon": "💎", "hp": 120, "str": 12, "mag": 20, "def": 13},
    "Beastkin":  {"rarity": "Rare",      "rarity_icon": "💎", "hp": 140, "str": 18, "mag": 8,  "def": 15},
    "Dragon-kin":{"rarity": "Primordial","rarity_icon": "👑", "hp": 200, "str": 30, "mag": 18, "def": 30},
    "Seraphim":  {"rarity": "Primordial","rarity_icon": "👑", "hp": 200, "str": 25, "mag": 30, "def": 25},
}

ORIGIN_TEXT = {
    "Normal": "You were born into this world like any other soul. A new life, a blank slate. Your story begins now.",
    "Reincarnation": "You remember it clearly — the moment your previous life ended. But fate wasn't done with you. You've been given another chance.",
    "Teleported": "One moment you were living your normal life. The next — you were ripped from your world without warning and thrown into this one."
}

ORIGIN_ICONS = {
    "Normal": "🌱",
    "Reincarnation": "🔄",
    "Teleported": "⚡"
}

def format_num(n):
    n = int(n)
    if n >= 1_000_000_000:
        v = n / 1_000_000_000
        return f"{v:.1f}B".replace('.0B', 'B')
    if n >= 1_000_000:
        v = n / 1_000_000
        return f"{v:.1f}M".replace('.0M', 'M')
    if n >= 1_000:
        v = n / 1_000
        return f"{v:.1f}K".replace('.0K', 'K')
    return str(n)

def parse_amount(s):
    s = str(s).lower().strip().replace(',', '')
    try:
        if s.endswith('b'):
            return int(float(s[:-1]) * 1_000_000_000)
        elif s.endswith('m'):
            return int(float(s[:-1]) * 1_000_000)
        elif s.endswith('k'):
            return int(float(s[:-1]) * 1_000)
        else:
            return int(float(s))
    except (ValueError, TypeError):
        raise ValueError(f"Invalid amount: {s}")

EXPLORE_ITEMS = [
    {"name": "Slime Jelly", "rarity": "Common", "type": "material"},
    {"name": "Rusty Dagger", "rarity": "Common", "type": "weapon"},
    {"name": "Sharp Thorn", "rarity": "Common", "type": "material"},
    {"name": "Torn Fur", "rarity": "Common", "type": "material"},
    {"name": "Weak Venom Pod", "rarity": "Common", "type": "material"},
    {"name": "Luminescent Spores", "rarity": "Common", "type": "material"},
    {"name": "Ancient Bone", "rarity": "Common", "type": "material"},
    {"name": "Putrid Flesh", "rarity": "Common", "type": "material"},
    {"name": "Ectoplasm", "rarity": "Uncommon", "type": "material"},
    {"name": "Iron Ore Fragment", "rarity": "Uncommon", "type": "material"},
    {"name": "Contaminated Tooth", "rarity": "Uncommon", "type": "material"},
    {"name": "Dark Cloth", "rarity": "Uncommon", "type": "material"},
    {"name": "Fire Scale", "rarity": "Uncommon", "type": "material"},
    {"name": "Sulfuric Ash", "rarity": "Uncommon", "type": "material"},
    {"name": "Ember Core", "rarity": "Uncommon", "type": "material"},
    {"name": "Winter Pelt", "rarity": "Uncommon", "type": "material"},
]

item_counters = {}

def generate_item_id(item_type):
    prefix_map = {
        "weapon": "W",
        "head_armor": "HA",
        "body_armor": "BA",
        "pet": "P",
        "consumable": "C",
        "material": "M",
        "drop": "D",
    }
    prefix = prefix_map.get(item_type, "I")
    if prefix not in item_counters:
        item_counters[prefix] = 1
    else:
        item_counters[prefix] += 1
    return f"{prefix}{str(item_counters[prefix]).zfill(3)}"


class PvPAcceptView(discord.ui.View):
    def __init__(self, ctx, opponent):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.opponent = opponent
        self.accepted = False

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("This challenge isn't for you!", ephemeral=True)
            return
        self.accepted = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("This challenge isn't for you!", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=discord.Embed(description="❌ Challenge declined.", color=0xFFD700), view=None)
        self.stop()


class Economy(commands.Cog, name="Economy"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="start")
    async def start(self, ctx):
        user_id = str(ctx.author.id)
        if players.search(Player.id == user_id):
            embed = discord.Embed(
                title="⚠️ Already Registered",
                description="You have already begun your journey!\nUse **!profile** to view your stats.",
                color=GOLD)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed)
            return

        from main import RACE_POOL_NORMAL, RACE_POOL_REINCARNATION, RACE_POOL_TELEPORTED
        origin = random.choices(ORIGINS, weights=ORIGIN_WEIGHTS, k=1)[0]

        if origin == "Reincarnation":
            race_name = random.choice(RACE_POOL_REINCARNATION)
        elif origin == "Teleported":
            race_name = random.choice(RACE_POOL_TELEPORTED)
        else:
            race_name = random.choice(RACE_POOL_NORMAL)

        stats = RACES[race_name]

        players.insert({
            "id": user_id,
            "name": ctx.author.name,
            "race": race_name,
            "origin": origin,
            "hp": stats["hp"],
            "str": stats["str"],
            "mag": stats["mag"],
            "def": stats["def"],
            "nexcoins": 1500,
            "starshards": 0,
            "votes": 0,
            "vote_streak": 0,
            "last_vote": 0,
            "level": 1,
            "exp": 0,
            "unspent_points": 0,
            "last_daily": 0,
            "last_hourly": 0,
            "last_explore": 0,
            "current_arc": 1,
            "current_enemy": 1,
            "inventory": [],
            "equipped": {
                "weapon": None,
                "head_armor": None,
                "body_armor": None,
                "pet": None
            },
            "rebirths": 0,
            "rebirth_bonus": 0,
            "banned": False,
            "ban_expiry": None,
            "guild_rank": "F",
            "guild_rep": 0,
            "clan_coins": 0,
            "active_quests": [],
            "quest_board": [],
            "quest_board_refreshed": 0,
            "last_gather": 0,
        })

        embed = discord.Embed(
            title="✨ A New Soul Enters Nexworld ✨",
            description=f"*{ORIGIN_TEXT[origin]}*",
            color=GOLD)
        embed.add_field(
            name="━━━━━━━━━━━━━━━━━━━━━━",
            value=f"{ORIGIN_ICONS[origin]} **Origin:** {origin}\n{stats['rarity_icon']} **Race:** {race_name} `{stats['rarity']}`",
            inline=False)
        embed.add_field(name="❤️ HP", value=f"`{stats['hp']}`", inline=True)
        embed.add_field(name="⚔️ STR", value=f"`{stats['str']}`", inline=True)
        embed.add_field(name="✨ MAG", value=f"`{stats['mag']}`", inline=True)
        embed.add_field(name="🛡️ DEF", value=f"`{stats['def']}`", inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="💰 Nexcoins", value="`1,500`", inline=True)
        embed.add_field(name="✨ Starshards", value="`0`", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="daily")
    async def daily(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        p = p[0]
        if p.get('banned', False):
            await ctx.send(embed=discord.Embed(description="❌ You are banned from Nexworld!", color=GOLD))
            return

        now = time.time()
        if now - p.get('last_daily', 0) < 86400:
            remaining = 86400 - (now - p.get('last_daily', 0))
            h = int(remaining // 3600)
            m = int((remaining % 3600) // 60)
            await ctx.send(embed=discord.Embed(
                title="⏰ Daily Already Claimed",
                description=f"Come back in **{h}h {m}m**!",
                color=GOLD))
            return

        reward_nc = random.randint(7000, 15000)
        reward_exp = random.randint(700, 1200)
        new_coins = p.get('nexcoins', 0) + reward_nc
        new_exp = p.get('exp', 0) + reward_exp
        players.update({'nexcoins': new_coins, 'exp': new_exp, 'last_daily': now}, Player.id == user_id)

        embed = discord.Embed(title="🎁 Daily Reward!", color=GOLD)
        embed.add_field(name="💰 Nexcoins", value=f"`+{reward_nc:,}`", inline=True)
        embed.add_field(name="⭐ EXP", value=f"`+{reward_exp:,}`", inline=True)
        embed.add_field(name="💰 New Balance", value=f"`{new_coins:,}`", inline=False)
        embed.set_footer(text="Nexworld RPG • Come back tomorrow!")
        await ctx.send(embed=embed)

    @commands.command(name="hourly", aliases=["hr"])
    async def hourly(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        p = p[0]
        if p.get('banned', False):
            await ctx.send(embed=discord.Embed(description="❌ You are banned from Nexworld!", color=GOLD))
            return
        now = time.time()
        if now - p.get('last_hourly', 0) < 3600:
            remaining = 3600 - (now - p.get('last_hourly', 0))
            m = int(remaining // 60)
            s = int(remaining % 60)
            await ctx.send(embed=discord.Embed(
                title="⏰ Hourly Already Claimed",
                description=f"Come back in **{m}m {s}s**!",
                color=GOLD))
            return
        reward_nc = random.randint(1000, 3000)
        reward_exp = random.randint(300, 500)
        new_coins = p.get('nexcoins', 0) + reward_nc
        new_exp = p.get('exp', 0) + reward_exp
        players.update({'nexcoins': new_coins, 'exp': new_exp, 'last_hourly': now}, Player.id == user_id)
        try:
            from quest_tracker import track_quest_progress
            track_quest_progress(user_id, 'hourly', 1)
        except Exception:
            pass
        embed = discord.Embed(title="⏰ Hourly Reward!", color=GOLD)
        embed.add_field(name="💰 Nexcoins", value=f"`+{reward_nc:,}`", inline=True)
        embed.add_field(name="⭐ EXP", value=f"`+{reward_exp:,}`", inline=True)
        embed.add_field(name="💰 New Balance", value=f"`{new_coins:,}`", inline=False)
        embed.set_footer(text="Nexworld RPG • Come back in an hour!")
        await ctx.send(embed=embed)

    @commands.command(name="fight")
    async def fight(self, ctx, opponent: discord.Member = None):
        if not opponent:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!fight @user`",
                color=GOLD))
            return
        if opponent.bot or opponent.id == ctx.author.id:
            await ctx.send(embed=discord.Embed(
                description="❌ Invalid opponent!",
                color=GOLD))
            return

        challenger_id = str(ctx.author.id)
        defender_id = str(opponent.id)

        cp = players.search(Player.id == challenger_id)
        dp = players.search(Player.id == defender_id)
        if not cp:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        if not dp:
            await ctx.send(embed=discord.Embed(description="❌ That player hasn't started yet!", color=GOLD))
            return
        cp, dp = cp[0], dp[0]
        if cp.get('banned', False) or dp.get('banned', False):
            await ctx.send(embed=discord.Embed(description="❌ One of the players is banned!", color=GOLD))
            return

        accept_view = PvPAcceptView(ctx, opponent)
        challenge_embed = discord.Embed(
            title="⚔️ PvP Challenge!",
            description=f"{ctx.author.mention} challenges {opponent.mention} to a duel!\n\n{opponent.mention}, do you accept?",
            color=GOLD)
        challenge_embed.set_footer(text="30 seconds to respond")
        await ctx.send(embed=challenge_embed, view=accept_view)
        await accept_view.wait()

        if not accept_view.accepted:
            await ctx.send(embed=discord.Embed(
                description=f"❌ **{opponent.display_name}** declined the challenge.",
                color=GOLD))
            return

        cp = players.search(Player.id == challenger_id)[0]
        dp = players.search(Player.id == defender_id)[0]
        def get_effective_stats(p):
            now = time.time()
            str_bonus = 100 if now < p.get('buff_str_boost_until', 0) else 0
            def_bonus = 100 if now < p.get('buff_def_boost_until', 0) else 0
            eq = p.get('equipped', {})
            inv = {}
            for i in p.get('inventory', []):
                uid_val = i.get('uid')
                if uid_val and isinstance(uid_val, str):
                    inv[uid_val] = i
            atk = p['str'] + str_bonus
            mag = p['mag'] + str_bonus
            defense = p['def'] + def_bonus
            for slot in ['weapon', 'body_armor', 'head_armor']:
                uid = eq.get(slot)
                if not uid or not isinstance(uid, str):
                    continue
                if uid in inv:
                    item = inv[uid]
                    stats = item.get('stats', {})
                    atk += stats.get('str', 0)
                    mag += stats.get('mag', 0)
                    defense += stats.get('def', 0)
            best_atk = max(atk, mag)
            hp = p['hp']
            return best_atk, defense, hp

        c_atk, c_def, c_hp = get_effective_stats(cp)
        d_atk, d_def, d_hp = get_effective_stats(dp)

        c_cur_hp = c_hp
        d_cur_hp = d_hp
        log_lines = []
        for rnd in range(1, 11):
            c_dmg = max(1, c_atk - d_def // 2)
            d_dmg = max(1, d_atk - c_def // 2)
            d_cur_hp -= c_dmg
            c_cur_hp -= d_dmg
            log_lines.append(f"**R{rnd}**: {ctx.author.display_name} deals `{c_dmg}` | {opponent.display_name} deals `{d_dmg}`")
            if d_cur_hp <= 0 or c_cur_hp <= 0:
                break

        c_cur_hp = max(0, c_cur_hp)
        d_cur_hp = max(0, d_cur_hp)

        if c_cur_hp > d_cur_hp:
            winner, loser = ctx.author, opponent
        elif d_cur_hp > c_cur_hp:
            winner, loser = opponent, ctx.author
        else:
            winner = loser = None

        reward = random.randint(2000, 5000)
        result_embed = discord.Embed(title="⚔️ PvP Battle Result!", color=GOLD)
        result_embed.add_field(name="📋 Battle Log", value="\n".join(log_lines[-5:]), inline=False)
        try:
            from quest_tracker import track_quest_progress
            track_quest_progress(challenger_id, 'fight', 1)
            track_quest_progress(defender_id, 'fight', 1)
        except Exception:
            pass
        if winner:
            winner_id = str(winner.id)
            loser_id = str(loser.id)
            wp = players.search(Player.id == winner_id)[0]
            players.update({'nexcoins': wp['nexcoins'] + reward}, Player.id == winner_id)
            result_embed.add_field(name="🏆 Winner", value=f"{winner.mention} wins `{reward:,}` Nexcoins!", inline=False)
            try:
                from quest_tracker import track_quest_progress
                track_quest_progress(winner_id, 'fight_win', 1)
            except Exception:
                pass
        else:
            result_embed.add_field(name="🤝 Draw", value="Both fighters are equal!", inline=False)
        result_embed.set_footer(text="Nexworld RPG • Fight again with !fight")
        await ctx.send(embed=result_embed)

    @commands.command(name="explore")
    async def explore(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        p = p[0]
        if p.get('banned', False):
            await ctx.send(embed=discord.Embed(description="❌ You are banned from Nexworld!", color=GOLD))
            return

        now = time.time()
        if now - p.get('last_explore', 0) < 3600:
            remaining = 3600 - (now - p.get('last_explore', 0))
            m = int(remaining // 60)
            s = int(remaining % 60)
            await ctx.send(embed=discord.Embed(
                title="⏰ Already Explored",
                description=f"Explore again in **{m}m {s}s**!",
                color=GOLD))
            return

        coins_gain = random.randint(500, 4500)
        exp_gain = random.randint(20, 80)
        if time.time() < p.get('buff_exp_boost_until', 0):
            exp_gain = int(exp_gain * 2)
        luck_active = time.time() < p.get('buff_luck_until', 0)
        if luck_active:
            rarity_weights = {'Common': 2, 'Uncommon': 5, 'Rare': 8, 'Epic': 5, 'Legendary': 3}
            item = random.choices(EXPLORE_ITEMS, weights=[rarity_weights.get(i['rarity'], 2) for i in EXPLORE_ITEMS])[0]
        else:
            item = random.choice(EXPLORE_ITEMS)

        all_items = players.search(Player.id == user_id)[0].get('inventory', [])
        existing_ids = [i.get('uid', '') for i in all_items]
        counter = len([i for i in existing_ids if i.startswith('M')]) + 1
        uid = f"M{str(counter).zfill(3)}"

        new_item = {
            'uid': uid,
            'name': item['name'],
            'rarity': item['rarity'],
            'type': item['type']
        }

        new_inv = all_items + [new_item]

        current_exp = p.get('exp', 0) + exp_gain
        current_level = p.get('level', 1)
        hp = p.get('hp', 100)
        str_ = p.get('str', 10)
        mag = p.get('mag', 10)
        def_ = p.get('def', 10)
        leveled_up = False
        old_level = current_level

        from main import get_stat_increase, exp_required
        while current_exp >= exp_required(current_level):
            current_exp -= exp_required(current_level)
            current_level += 1
            increase = get_stat_increase(current_level)
            hp += increase['hp']
            str_ += increase['str']
            mag += increase['mag']
            def_ += increase['def']
            leveled_up = True

        new_coins = p.get('nexcoins', 0) + coins_gain

        players.update({
            'last_explore': now,
            'inventory': new_inv,
            'exp': current_exp,
            'level': current_level,
            'hp': hp,
            'str': str_,
            'mag': mag,
            'def': def_,
            'nexcoins': new_coins
        }, Player.id == user_id)
        try:
            from quest_tracker import track_quest_progress
            track_quest_progress(user_id, 'explore', 1)
        except Exception:
            pass

        zone = random.choice(EXPLORE_ZONES)
        embed = discord.Embed(
            title=f"🗺️ {zone['name']}",
            description=zone['flavor'],
            color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="🎁 Item Found", value=f"**{item['name']}** `{item['rarity']}`\nID: `{uid}`", inline=False)
        embed.add_field(name="💰 Nexcoins", value=f"`+{coins_gain:,}`", inline=True)
        embed.add_field(name="🔮 EXP", value=f"`+{format_num(exp_gain)}`", inline=True)
        if leveled_up:
            embed.add_field(name="⬆️ LEVEL UP!", value=f"**{old_level} → {current_level}**\nStats automatically increased!", inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="⏰ Cooldown", value="Explore again in **1 hour**!", inline=False)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        img_path = os.path.join(_STATIC_DIR, zone['img'])
        if os.path.exists(img_path):
            file = discord.File(img_path, filename=zone['img'])
            embed.set_image(url=f"attachment://{zone['img']}")
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed, file=file)
        else:
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed)

    @commands.command(name="vote")
    async def vote(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        p = p[0]
        streak = p.get('vote_streak', 0)
        total_votes = p.get('votes', 0)
        streak_rewards = {1: 1000, 2: 2500, 3: 5000, 4: 8000, 5: 12000, 6: 18000}
        coin_reward = streak_rewards.get(max(1, streak), 25000)

        embed = discord.Embed(title="🗳️ Vote for Nexworld!", color=GOLD)
        embed.add_field(name="Vote Link", value="[Click here to vote!](https://top.gg/bot/YOUR_BOT_ID)", inline=False)
        embed.add_field(name="Rewards", value=f"💰 **{coin_reward:,} Nexcoins**\n✨ **10 Starshards** (40% chance)", inline=False)
        embed.add_field(name="🔥 Streaks", value="x1: 1,000\nx2: 2,500\nx3: 5,000\nx4: 8,000\nx5: 12,000\nx6: 18,000\nx7+: 25,000", inline=False)
        embed.add_field(name="📊 Your Stats", value=f"Total: `{total_votes}` • Streak: `x{streak}`", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="pay")
    async def pay(self, ctx, member: discord.Member = None, amount: str = None):
        if not member or amount is None:
            await ctx.send(embed=discord.Embed(description="Usage: `!pay @user <amount>`\nShortcuts: `10k` = 10,000 • `1m` = 1,000,000", color=GOLD))
            return
        if member.id == ctx.author.id:
            await ctx.send(embed=discord.Embed(description="❌ Can't pay yourself!", color=GOLD))
            return

        try:
            amount_int = parse_amount(amount)
        except ValueError:
            await ctx.send(embed=discord.Embed(description="❌ Invalid amount! Use numbers like `1000`, `10k`, or `1m`.", color=GOLD))
            return

        if amount_int <= 0:
            await ctx.send(embed=discord.Embed(description="❌ Amount must be greater than 0!", color=GOLD))
            return

        user_id = str(ctx.author.id)
        target_id = str(member.id)

        sender_data = players.search(Player.id == user_id)
        target_data = players.search(Player.id == target_id)

        if not sender_data:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        if not target_data:
            await ctx.send(embed=discord.Embed(description="❌ That player hasn't started yet!", color=GOLD))
            return

        sender = sender_data[0]
        target = target_data[0]

        if sender.get('nexcoins', 0) < amount_int:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Not enough Nexcoins!\nYour balance: `{sender.get('nexcoins', 0):,}`",
                color=GOLD))
            return

        sender_new = sender.get('nexcoins', 0) - amount_int
        target_new = target.get('nexcoins', 0) + amount_int

        players.update({'nexcoins': sender_new}, Player.id == user_id)
        players.update({'nexcoins': target_new}, Player.id == target_id)

        embed = discord.Embed(title="💰 Payment Sent!", color=GOLD)
        embed.add_field(name="Amount", value=f"`{amount_int:,}` Nexcoins → {member.mention}", inline=False)
        embed.add_field(name="Your Balance", value=f"`{sender_new:,}`", inline=True)
        embed.add_field(name=f"{member.name}'s Balance", value=f"`{target_new:,}`", inline=True)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="payss")
    async def payss(self, ctx, member: discord.Member = None, amount: int = None):
        if not member or amount is None:
            await ctx.send(embed=discord.Embed(description="Usage: `!payss @user <amount>`", color=GOLD))
            return
        if member.id == ctx.author.id:
            await ctx.send(embed=discord.Embed(description="❌ Can't pay yourself!", color=GOLD))
            return

        user_id = str(ctx.author.id)
        target_id = str(member.id)

        sender_data = players.search(Player.id == user_id)
        target_data = players.search(Player.id == target_id)

        if not sender_data:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        if not target_data:
            await ctx.send(embed=discord.Embed(description="❌ That player hasn't started yet!", color=GOLD))
            return

        sender = sender_data[0]
        target = target_data[0]

        if amount <= 0:
            await ctx.send(embed=discord.Embed(description="❌ Amount must be greater than 0!", color=GOLD))
            return
        if sender.get('starshards', 0) < amount:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Not enough Starshards!\nYour balance: `{sender.get('starshards', 0):,}`",
                color=GOLD))
            return

        sender_new = sender.get('starshards', 0) - amount
        target_new = target.get('starshards', 0) + amount

        players.update({'starshards': sender_new}, Player.id == user_id)
        players.update({'starshards': target_new}, Player.id == target_id)

        embed = discord.Embed(title="✨ Starshards Sent!", color=GOLD)
        embed.add_field(name="Amount", value=f"`{amount:,}` Starshards → {member.mention}", inline=False)
        embed.add_field(name="Your Balance", value=f"`{sender_new:,}`", inline=True)
        embed.add_field(name=f"{member.name}'s Balance", value=f"`{target_new:,}`", inline=True)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="market")
    async def market(self, ctx):
        listings = sorted(market_table.all(), key=lambda x: x.get('price', 0))
        embed = discord.Embed(title="🏪 Nexworld Market", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        if not listings:
            embed.add_field(name="Empty", value="No listings!\nUse `!ma <item id> <price>` to list items.", inline=False)
        else:
            for l in listings[:10]:
                embed.add_field(
                    name=f"(`{l['listing_id']}`) {l['item_name']} — `{l['rarity']}`",
                    value=f"Price: `{l['price']:,}` Nexcoins • Seller: {l['seller_name']}",
                    inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="Commands", value="`!mb <id>` — Buy\n`!ma <item id> <price>` — List\n`!mr <listing id>` — Remove", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="marketadd", aliases=["ma"])
    async def marketadd(self, ctx, item_uid: str = None, price: int = None):
        if not item_uid or price is None:
            await ctx.send(embed=discord.Embed(description="Usage: `!ma <item id> <price>`", color=GOLD))
            return

        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        inventory = p.get('inventory', [])
        item = next((i for i in inventory if i['uid'] == item_uid), None)

        if not item:
            await ctx.send(embed=discord.Embed(description=f"❌ Item `{item_uid}` not found!", color=GOLD))
            return
        if price <= 0:
            await ctx.send(embed=discord.Embed(description="❌ Price must be greater than 0!", color=GOLD))
            return

        all_listings = market_table.all()
        listing_num = len(all_listings) + 1
        listing_id = f"L{str(listing_num).zfill(3)}"

        market_table.insert({
            'listing_id': listing_id,
            'seller_id': user_id,
            'seller_name': ctx.author.name,
            'item_uid': item_uid,
            'item_name': item['name'],
            'rarity': item['rarity'],
            'price': price
        })

        new_inv = [i for i in inventory if i['uid'] != item_uid]
        players.update({'inventory': new_inv}, Player.id == user_id)

        embed = discord.Embed(
            title="✅ Item Listed!",
            description=f"**{item['name']}** listed for `{price:,}` Nexcoins!\nListing ID: `{listing_id}`",
            color=GOLD)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="marketremove", aliases=["mr"])
    async def marketremove(self, ctx, listing_id: str = None):
        if not listing_id:
            await ctx.send(embed=discord.Embed(description="Usage: `!mr <listing id>`", color=GOLD))
            return

        user_id = str(ctx.author.id)
        listing = market_table.search(Market.listing_id == listing_id)

        if not listing:
            await ctx.send(embed=discord.Embed(description=f"❌ Listing `{listing_id}` not found!", color=GOLD))
            return

        listing = listing[0]
        if listing['seller_id'] != user_id:
            await ctx.send(embed=discord.Embed(description="❌ You can only remove your own listings!", color=GOLD))
            return

        p = players.search(Player.id == user_id)
        if p:
            inv = p[0].get('inventory', [])
            inv.append({
                'uid': listing['item_uid'],
                'name': listing['item_name'],
                'rarity': listing['rarity'],
                'type': 'returned'
            })
            players.update({'inventory': inv}, Player.id == user_id)

        market_table.remove(Market.listing_id == listing_id)
        await ctx.send(embed=discord.Embed(
            title="✅ Listing Removed!",
            description=f"**{listing['item_name']}** returned to inventory!",
            color=GOLD))

    @commands.command(name="marketbuy", aliases=["mb"])
    async def marketbuy(self, ctx, listing_id: str = None):
        if not listing_id:
            await ctx.send(embed=discord.Embed(description="Usage: `!mb <listing id>`", color=GOLD))
            return

        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        listing = market_table.search(Market.listing_id == listing_id)

        if not listing:
            await ctx.send(embed=discord.Embed(description=f"❌ Listing `{listing_id}` not found!", color=GOLD))
            return

        listing = listing[0]
        if listing['seller_id'] == user_id:
            await ctx.send(embed=discord.Embed(description="❌ Can't buy your own listing!", color=GOLD))
            return
        if p.get('nexcoins', 0) < listing['price']:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Not enough Nexcoins!\nPrice: `{listing['price']:,}` • Balance: `{p.get('nexcoins', 0):,}`",
                color=GOLD))
            return

        buyer_new = p.get('nexcoins', 0) - listing['price']
        players.update({'nexcoins': buyer_new}, Player.id == user_id)

        seller = players.search(Player.id == listing['seller_id'])
        if seller:
            seller_new = seller[0].get('nexcoins', 0) + listing['price']
            players.update({'nexcoins': seller_new}, Player.id == listing['seller_id'])

        inv = p.get('inventory', [])
        inv.append({
            'uid': listing['item_uid'],
            'name': listing['item_name'],
            'rarity': listing['rarity'],
            'type': 'purchased'
        })
        players.update({'inventory': inv}, Player.id == user_id)
        market_table.remove(Market.listing_id == listing_id)

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"Bought **{listing['item_name']}** for `{listing['price']:,}` Nexcoins!",
            color=GOLD)
        embed.add_field(name="💰 New Balance", value=f"`{buyer_new:,}`", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="use")
    async def use(self, ctx, item_uid: str = None):
        if not item_uid:
            await ctx.send(embed=discord.Embed(description="Usage: `!use <item id>`", color=GOLD))
            return

        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        inventory = p.get('inventory', [])
        item = next((i for i in inventory if i['uid'] == item_uid), None)

        if not item:
            await ctx.send(embed=discord.Embed(description=f"❌ Item `{item_uid}` not found!", color=GOLD))
            return

        if item['name'] == 'Race Reroll Token':
            from main import RACE_POOL_REROLL
            new_race = random.choice(RACE_POOL_REROLL)
            stats = RACES[new_race]
            unspent = p.get('unspent_points', 0)

            total_returned = (
                max(0, p.get('str', 0) - stats['str']) +
                max(0, p.get('mag', 0) - stats['mag']) +
                max(0, p.get('def', 0) - stats['def']) +
                max(0, p.get('hp', 0) - stats['hp'])
            )

            new_inv = [i for i in inventory if i['uid'] != item_uid]
            players.update({
                'race': new_race,
                'hp': stats['hp'],
                'str': stats['str'],
                'mag': stats['mag'],
                'def': stats['def'],
                'unspent_points': unspent + total_returned,
                'inventory': new_inv
            }, Player.id == user_id)

            embed = discord.Embed(title="🎲 Race Rerolled!", description=f"New race: **{new_race}** `{stats['rarity']}`!", color=GOLD)
            embed.add_field(name="❤️ HP", value=f"`{stats['hp']}`", inline=True)
            embed.add_field(name="⚔️ STR", value=f"`{stats['str']}`", inline=True)
            embed.add_field(name="✨ MAG", value=f"`{stats['mag']}`", inline=True)
            embed.add_field(name="🛡️ DEF", value=f"`{stats['def']}`", inline=True)
            if total_returned > 0:
                embed.add_field(name="💡 Points Returned", value=f"`{total_returned}` back to unspent!", inline=False)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed)
        elif item['type'] == 'consumable':
            await ctx.send(embed=discord.Embed(
                description=f"💊 **{item['name']}** — Use this during battle for its effect!",
                color=GOLD))
        else:
            await ctx.send(embed=discord.Embed(
                description=f"**{item['name']}** `{item['rarity']}` — Use `!ie {item_uid}` to equip it!",
                color=GOLD))

    @commands.command(name="itemequip", aliases=["ie"])
    async def itemequip(self, ctx, item_uid: str = None):
        if not item_uid:
            await ctx.send(embed=discord.Embed(description="Usage: `!ie <item id>`", color=GOLD))
            return

        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        inventory = p.get('inventory', [])
        item = next((i for i in inventory if i['uid'] == item_uid), None)

        if not item:
            await ctx.send(embed=discord.Embed(description=f"❌ Item `{item_uid}` not found!", color=GOLD))
            return

        item_type = item.get('type', 'material')
        equipped = p.get('equipped', {"weapon": None, "head_armor": None, "body_armor": None, "pet": None})

        slot_map = {
            'weapon': 'weapon',
            'armor': 'body_armor',
            'head_armor': 'head_armor',
            'body_armor': 'body_armor',
            'pet': 'pet',
            'item': 'pet',
        }

        if item_type not in slot_map:
            await ctx.send(embed=discord.Embed(
                description=f"❌ **{item['name']}** cannot be equipped!",
                color=GOLD))
            return

        slot = slot_map[item_type]
        old_item = equipped.get(slot)

        hp  = p.get('hp',  100)
        str_ = p.get('str', 10)
        mag = p.get('mag', 10)
        def_ = p.get('def', 10)

        if old_item:
            for stat, val in old_item.get('stats', {}).items():
                if stat == 'hp':  hp   = max(1, hp   - val)
                if stat == 'str': str_ = max(1, str_ - val)
                if stat == 'mag': mag  = max(1, mag  - val)
                if stat == 'def': def_ = max(1, def_ - val)

        new_stats = item.get('stats', {})
        stat_lines = []
        for stat, val in new_stats.items():
            if stat == 'hp':  hp   += val; stat_lines.append(f"+{val} HP")
            if stat == 'str': str_ += val; stat_lines.append(f"+{val} STR")
            if stat == 'mag': mag  += val; stat_lines.append(f"+{val} MAG")
            if stat == 'def': def_ += val; stat_lines.append(f"+{val} DEF")

        equipped[slot] = {
            'uid': item['uid'],
            'name': item['name'],
            'rarity': item['rarity'],
            'stats': new_stats
        }

        players.update({
            'equipped': equipped,
            'hp': hp, 'str': str_, 'mag': mag, 'def': def_
        }, Player.id == user_id)

        embed = discord.Embed(
            title="✅ Item Equipped!",
            description=f"**{item['name']}** `{item['rarity']}` equipped!",
            color=GOLD)
        if stat_lines:
            embed.add_field(name="Stats Applied", value="\n".join(stat_lines), inline=False)
        if old_item:
            embed.add_field(name="Replaced", value=f"`{old_item['name']}`", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="itemunequip", aliases=["iue"])
    async def itemunequip(self, ctx, slot: str = None):
        valid_slots = ['weapon', 'head_armor', 'body_armor', 'pet']
        if not slot or slot.lower() not in valid_slots:
            await ctx.send(embed=discord.Embed(
                description=f"Usage: `!iue <slot>`\nSlots: `weapon`, `head_armor`, `body_armor`, `pet`",
                color=GOLD))
            return

        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        equipped = p.get('equipped', {"weapon": None, "head_armor": None, "body_armor": None, "pet": None})

        if not equipped.get(slot):
            await ctx.send(embed=discord.Embed(description=f"❌ Nothing equipped in `{slot}` slot!", color=GOLD))
            return

        item = equipped[slot]
        equipped[slot] = None

        hp   = p.get('hp',  100)
        str_ = p.get('str', 10)
        mag  = p.get('mag', 10)
        def_ = p.get('def', 10)
        for stat, val in item.get('stats', {}).items():
            if stat == 'hp':  hp   = max(1, hp   - val)
            if stat == 'str': str_ = max(1, str_ - val)
            if stat == 'mag': mag  = max(1, mag  - val)
            if stat == 'def': def_ = max(1, def_ - val)

        players.update({
            'equipped': equipped,
            'hp': hp, 'str': str_, 'mag': mag, 'def': def_
        }, Player.id == user_id)

        await ctx.send(embed=discord.Embed(
            title="✅ Item Unequipped!",
            description=f"**{item['name']}** removed from `{slot}` slot!\nStat bonuses removed.",
            color=GOLD))

    @commands.command(name="equipped")
    async def equipped(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
            return

        p = p[0]
        equipped = p.get('equipped', {"weapon": None, "head_armor": None, "body_armor": None, "pet": None})

        embed = discord.Embed(title=f"⚔️ {member.name}'s Equipped Items", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)

        slots = {
            "weapon": "⚔️ Weapon",
            "head_armor": "🪖 Head Armor",
            "body_armor": "🛡️ Body Armor",
            "pet": "🐾 Pet"
        }

        for slot_key, slot_name in slots.items():
            item = equipped.get(slot_key)
            if item:
                embed.add_field(
                    name=slot_name,
                    value=f"**{item['name']}** `{item['rarity']}`\nID: `{item['uid']}`",
                    inline=False)
            else:
                embed.add_field(name=slot_name, value="`None`", inline=False)

        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="rebirth")
    async def rebirth(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        if p.get('level', 1) < 1000:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Need level **1000** to rebirth!\nCurrent: `{p.get('level', 1)}`",
                color=GOLD))
            return

        class RebirthView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30)

            @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.green)
            async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Not your rebirth!", ephemeral=True)
                    return
                rebirths = p.get('rebirths', 0) + 1
                rebirth_bonus = rebirths * 10
                mult = 1 + rebirth_bonus / 100
                new_hp  = int(100 * mult)
                new_str = int(10  * mult)
                new_mag = int(10  * mult)
                new_def = int(10  * mult)
                for slot_item in p.get('equipped', {}).values():
                    if slot_item:
                        for stat, val in slot_item.get('stats', {}).items():
                            if stat == 'hp':  new_hp  += val
                            if stat == 'str': new_str += val
                            if stat == 'mag': new_mag += val
                            if stat == 'def': new_def += val
                players.update({
                    'level': 1, 'exp': 0,
                    'rebirths': rebirths,
                    'rebirth_bonus': rebirth_bonus,
                    'current_arc': 1,
                    'current_enemy': 1,
                    'unspent_points': 0,
                    'hp': new_hp, 'str': new_str, 'mag': new_mag, 'def': new_def
                }, Player.id == user_id)
                embed = discord.Embed(title="🔁 Rebirth Complete!", color=GOLD)
                embed.add_field(name="Rebirths", value=f"`{rebirths}`", inline=True)
                embed.add_field(name="Permanent Bonus", value=f"`+{rebirth_bonus}%` all stats!", inline=True)
                embed.add_field(name="New Stats", value=f"❤️ `{new_hp}` • ⚔️ `{new_str}` • ✨ `{new_mag}` • 🛡️ `{new_def}`", inline=False)
                embed.add_field(name="Kept", value="✅ Inventory • ✅ Nexcoins • ✅ Starshards", inline=False)
                embed.add_field(name="Reset", value="❌ Level • ❌ EXP • ❌ Arc Progress", inline=False)
                await interaction.response.edit_message(embed=embed, view=None)

            @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
            async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
                await interaction.response.edit_message(
                    embed=discord.Embed(description="Rebirth cancelled.", color=GOLD), view=None)

        rebirths = p.get('rebirths', 0)
        next_bonus = (rebirths + 1) * 10
        embed = discord.Embed(title="🔁 Confirm Rebirth?", color=GOLD)
        embed.add_field(name="Next Rebirth Bonus", value=f"`+{next_bonus}%` permanent stat boost!", inline=False)
        embed.add_field(name="Keep", value="✅ Inventory\n✅ Nexcoins\n✅ Starshards", inline=True)
        embed.add_field(name="Lose", value="❌ Level\n❌ EXP\n❌ Arc Progress", inline=True)
        await ctx.send(embed=embed, view=RebirthView())

    @commands.command(name="sell")
    async def sell(self, ctx, uid: str = None):
        if not uid:
            await ctx.send(embed=discord.Embed(description="Usage: `!sell <item_id>`\nSells materials and drops from your inventory.", color=GOLD))
            return
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        p = p[0]
        inv = p.get('inventory', [])
        item = next((i for i in inv if i.get('uid', '').lower() == uid.lower()), None)
        if not item:
            await ctx.send(embed=discord.Embed(description=f"❌ Item `{uid}` not found in your inventory!", color=GOLD))
            return
        _UNSELLABLE = ('weapon', 'armor', 'head_armor', 'body_armor', 'pet', 'buff', 'consumable', 'itempack', 'petpack')
        if item.get('type') in _UNSELLABLE:
            await ctx.send(embed=discord.Embed(
                description=f"❌ **{item['name']}** can't be sold!\nOnly materials, drops, and raid drops can be sold with `!sell`.",
                color=GOLD))
            return
        price_ranges = {
            'Common':     (100,   300),
            'Uncommon':   (300,   500),
            'Rare':       (500,   900),
            'Epic':       (900,   1500),
            'Legendary':  (1500,  3000),
            'Mythic':     (3000,  6000),
            'Divine':     (6000,  12000),
            'Celestial':  (10000, 25000),
        }
        rarity = item.get('rarity', 'Common')
        low, high = price_ranges.get(rarity, (100, 300))
        price = random.randint(low, high)
        inv.remove(item)
        new_coins = p.get('nexcoins', 0) + price
        players.update({'inventory': inv, 'nexcoins': new_coins}, Player.id == user_id)
        embed = discord.Embed(title="💰 Item Sold!", color=GOLD)
        embed.add_field(name="Item", value=f"**{item['name']}** `{rarity}`", inline=True)
        embed.add_field(name="Earned", value=f"`{price:,}` Nexcoins", inline=True)
        embed.add_field(name="New Balance", value=f"`{new_coins:,}` Nexcoins", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="cooldown", aliases=["cd"])
    async def cooldown(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        now = time.time()

        def fmt(last, secs):
            rem = secs - (now - last)
            if rem <= 0:
                return "✅ Ready!"
            h = int(rem // 3600)
            m = int((rem % 3600) // 60)
            s = int(rem % 60)
            if h > 0:
                return f"⏰ {h}h {m}m"
            elif m > 0:
                return f"⏰ {m}m {s}s"
            return f"⏰ {s}s"

        embed = discord.Embed(title=f"⏱️ {ctx.author.name}'s Cooldowns", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="📅 Daily", value=fmt(p.get('last_daily', 0), 86400), inline=True)
        embed.add_field(name="🗺️ Explore", value=fmt(p.get('last_explore', 0), 3600), inline=True)
        embed.add_field(name="🗳️ Vote", value=fmt(p.get('last_vote', 0), 43200), inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="setprefix")
    async def setprefix(self, ctx, new_prefix: str = None):
        if not new_prefix:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!setprefix <symbol>`\nAllowed: `! $ - * ? .`", color=GOLD))
            return
        if new_prefix not in ALLOWED_PREFIXES:
            await ctx.send(embed=discord.Embed(
                title="⚠️ Invalid Prefix",
                description=f"`{new_prefix}` not allowed!\nAllowed: `! $ - * ? .`", color=GOLD))
            return

        Prefix = Query()
        user_id = str(ctx.author.id)

        if prefixes_table.search(Prefix.id == user_id):
            prefixes_table.update({'prefix': new_prefix}, Prefix.id == user_id)
        else:
            prefixes_table.insert({'id': user_id, 'prefix': new_prefix})

        await ctx.send(embed=discord.Embed(
            title="✅ Prefix Updated!",
            description=f"Your prefix is now `{new_prefix}`\nExample: `{new_prefix}profile`",
            color=GOLD))

async def setup(bot):
    await bot.add_cog(Economy(bot))