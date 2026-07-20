import discord
from discord.ext import commands
from db import players, Player
from main import format_number

GOLD = 0xFFD700

RACES = {
    "Human":     {"rarity": "Common",    "rarity_icon": "⭐"},
    "Halfblood": {"rarity": "Common",    "rarity_icon": "⭐"},
    "Kobold":    {"rarity": "Common",    "rarity_icon": "⭐"},
    "Elf":       {"rarity": "Rare",      "rarity_icon": "💎"},
    "Beastkin":  {"rarity": "Rare",      "rarity_icon": "💎"},
    "Dragon-kin":{"rarity": "Primordial","rarity_icon": "👑"},
    "Seraphim":  {"rarity": "Primordial","rarity_icon": "👑"},
}

ORIGIN_ICONS = {
    "Normal": "🌱",
    "Reincarnation": "🔄",
    "Teleported": "⚡"
}

def exp_required(level):
    return int(100 * (1.5 ** (level - 1)))

class InvView(discord.ui.View):
    RARITY_ICONS = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵", "Epic": "🟣",
                    "Legendary": "🟠", "Mythic": "🔴", "Divine": "🟡", "Celestial": "💠", "Godly": "🔱"}
    PER_PAGE = 10

    def __init__(self, ctx, target, inv):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.target = target
        self.inv = inv
        self.page = 1

    def build_embed(self):
        total = len(self.inv)
        total_pages = max(1, (total + self.PER_PAGE - 1) // self.PER_PAGE)
        self.page = max(1, min(self.page, total_pages))
        start = (self.page - 1) * self.PER_PAGE
        page_items = self.inv[start:start + self.PER_PAGE]

        p = players.search(Player.id == str(self.target.id))
        equipped_uids = set()
        if p:
            eq = p[0].get('equipped', {})
            equipped_uids = {v['uid'] for v in eq.values() if v and isinstance(v, dict) and 'uid' in v}

        embed = discord.Embed(title=f"🎒 {self.target.name}'s Inventory", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        if not self.inv:
            embed.add_field(name="Empty", value="No items!\nBuy from `!shop` or earn from battles.", inline=False)
        else:
            items_text = ""
            for item in page_items:
                icon = self.RARITY_ICONS.get(item.get('rarity', ''), '❔')
                lock = " 🔒" if item.get('uid') in equipped_uids else ""
                items_text += f"{icon} `{item.get('uid','?')}` **{item['name']}** — `{item.get('rarity','?')}`{lock}\n"
            embed.add_field(name=f"Items ({start+1}–{min(start+self.PER_PAGE, total)} of {total})", value=items_text or "—", inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="Commands", value="`!ie <id>` Equip • `!iue <slot>` Unequip • `!usebuff <id>` Use Buff • `!sell <id>` Sell • `!ma <id> <price>` Market", inline=False)
        embed.set_thumbnail(url=self.target.display_avatar.url)
        embed.set_footer(text=f"Page {self.page}/{total_pages} • Nexworld RPG")
        return embed

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.grey)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your inventory!", ephemeral=True)
            return
        if self.page > 1:
            self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.grey)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your inventory!", ephemeral=True)
            return
        total_pages = max(1, (len(self.inv) + self.PER_PAGE - 1) // self.PER_PAGE)
        if self.page < total_pages:
            self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class LbView(discord.ui.View):
    PER_PAGE = 10
    RANK_ORDER_LB = ["F", "E", "D", "C", "B", "A", "S"]
    RANK_ICONS_LB = {"F": "🩶", "E": "🤍", "D": "🩵", "C": "💚", "B": "💛", "A": "🧡", "S": "❤️"}

    CATEGORIES = {
        "level":      ("⚡ Leaderboard — Level",      lambda p: p.get('level', 1),      lambda p: f"Level {p.get('level', 1):,}"),
        "coins":      ("💰 Leaderboard — Nexcoins",    lambda p: p.get('nexcoins', 0),    lambda p: f"{p.get('nexcoins', 0):,} NC"),
        "starshards": ("✨ Leaderboard — Starshards",  lambda p: p.get('starshards', 0),  lambda p: f"{p.get('starshards', 0):,} SS"),
        "guildrank":  ("🎖️ Leaderboard — Guild Rank", lambda p: LbView.RANK_ORDER_LB.index(p.get('guild_rank', 'F')) if p.get('guild_rank', 'F') in LbView.RANK_ORDER_LB else 0, lambda p: f"{LbView.RANK_ICONS_LB.get(p.get('guild_rank', 'F'), '🩶')} {p.get('guild_rank', 'F')}-Rank"),
    }

    def __init__(self, ctx, category="level"):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.category = category
        self.page = 1

    def build_embed(self):
        all_players = players.all()
        title, key_fn, val_fn = self.CATEGORIES[self.category]
        sorted_p = sorted(all_players, key=key_fn, reverse=True)
        total = len(sorted_p)
        total_pages = max(1, (total + self.PER_PAGE - 1) // self.PER_PAGE)
        self.page = max(1, min(self.page, total_pages))
        start = (self.page - 1) * self.PER_PAGE
        page_players = sorted_p[start:start + self.PER_PAGE]

        embed = discord.Embed(title=title, color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        medals = ["🥇", "🥈", "🥉"]
        lb_text = ""
        for i, player in enumerate(page_players):
            rank = start + i
            medal = medals[rank] if rank < 3 else f"`#{rank+1}`"
            lb_text += f"{medal} **{player['name']}** — {val_fn(player)}\n"
        embed.add_field(name=f"Rankings ({start+1}–{min(start+self.PER_PAGE, total)} of {total})", value=lb_text or "No players yet!", inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.set_footer(text=f"Page {self.page}/{total_pages} • Use buttons to change page or category")
        return embed

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.grey, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        if self.page > 1:
            self.page -= 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.grey, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        total_pages = max(1, (len(players.all()) + self.PER_PAGE - 1) // self.PER_PAGE)
        if self.page < total_pages:
            self.page += 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="⚡ Level", style=discord.ButtonStyle.blurple, row=1)
    async def cat_level(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        self.category = "level"
        self.page = 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="💰 Nexcoins", style=discord.ButtonStyle.blurple, row=1)
    async def cat_coins(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        self.category = "coins"
        self.page = 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="✨ Starshards", style=discord.ButtonStyle.blurple, row=1)
    async def cat_ss(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        self.category = "starshards"
        self.page = 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="🎖️ Guild Rank", style=discord.ButtonStyle.blurple, row=1)
    async def cat_guildrank(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        self.category = "guildrank"
        self.page = 1
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class Profile(commands.Cog, name="Profile"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="profile", aliases=["pf"])
    async def profile(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(
                description=f"❌ {member.name} hasn't started yet!", color=GOLD))
            return

        p = p[0]
        from cogs.guild import get_rank_icon
        race_data = RACES.get(p['race'], {"rarity": "Unknown", "rarity_icon": "❓"})
        level = p.get('level', 1)
        exp = p.get('exp', 0)
        exp_needed = exp_required(level)
        rebirths = p.get('rebirths', 0)
        rebirth_bonus = p.get('rebirth_bonus', 0)
        equipped = p.get('equipped', {})

        embed = discord.Embed(title=f"📜 {member.name}'s Chronicle", color=GOLD)
        embed.add_field(
            name="🌍 Identity",
            value=f"{race_data['rarity_icon']} **Race:** {p['race']} `{race_data['rarity']}`\n"
                  f"{ORIGIN_ICONS.get(p['origin'], '❓')} **Origin:** {p['origin']}\n"
                  f"⚡ **Level:** {level}\n"
                  f"🎖️ **Guild Rank:** {get_rank_icon(p.get('guild_rank', 'F'))} {p.get('guild_rank', 'F')}-Rank\n"
                  f"🔮 **EXP:** {format_number(exp)} / {format_number(exp_needed)}\n"
                  f"🔁 **Rebirths:** {rebirths}" + (f" `+{rebirth_bonus}% stats`" if rebirths > 0 else ""),
            inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="❤️ HP", value=f"`{format_number(p['hp'])}`", inline=True)
        embed.add_field(name="⚔️ STR", value=f"`{format_number(p['str'])}`", inline=True)
        embed.add_field(name="✨ MAG", value=f"`{format_number(p['mag'])}`", inline=True)
        embed.add_field(name="🛡️ DEF", value=f"`{format_number(p['def'])}`", inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(
            name="💰 Balance",
            value=f"Nexcoins: `{format_number(p.get('nexcoins', 0))}`\nStarshards: `{format_number(p.get('starshards', 0))}`",
            inline=False)

        weapon = equipped.get('weapon')
        head = equipped.get('head_armor')
        body = equipped.get('body_armor')
        pet = equipped.get('pet')

        equipped_text = (
            f"🪖 Head: `{head['name'] if head else 'None'}`\n"
            f"🛡️ Body: `{body['name'] if body else 'None'}`\n"
            f"⚔️ Weapon: `{weapon['name'] if weapon else 'None'}`\n"
            f"🐾 Pet: `{pet['name'] if pet else 'None'}`"
        )
        embed.add_field(name="🎽 Equipped", value=equipped_text, inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="points")
    async def points(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
            return
        p = p[0]
        unspent = p.get('unspent_points', 0)
        embed = discord.Embed(title=f"✨ {member.name}'s Unspent Points", color=GOLD)
        embed.add_field(name="Unspent Points", value=f"`{unspent:,}`", inline=False)
        embed.add_field(
            name="Current Stats",
            value=f"❤️ HP: `{p.get('hp', 0):,}` • ⚔️ STR: `{p.get('str', 0):,}` • ✨ MAG: `{p.get('mag', 0):,}` • 🛡️ DEF: `{p.get('def', 0):,}`",
            inline=False)
        if unspent > 0:
            embed.add_field(name="How to Spend", value="Use `!assign <stat> <amount>`\nValid stats: `hp`, `str`, `mag`, `def`", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
            return
        p = p[0]
        embed = discord.Embed(title=f"💰 {member.name}'s Balance", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="Nexcoins", value=f"`{p.get('nexcoins', 0):,}`", inline=True)
        embed.add_field(name="Starshards", value=f"`{p.get('starshards', 0):,}`", inline=True)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx, member: discord.Member = None):
        target = member or ctx.author
        user_id = str(target.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
            return
        inv = p[0].get('inventory', [])
        view = InvView(ctx, target, inv)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="skills")
    async def skills(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
            return

        p = p[0]
        race = p['race']
        level = p.get('level', 1)

        from main import RACE_SKILLS, get_skill_name, get_skill_effect
        race_skills = RACE_SKILLS[race]
        special = race_skills['special']

        def describe_effect(effect):
            if not effect:
                return "Deals damage."
            t = effect.get('type')
            if t == 'damage':
                return f"Deals damage ({effect.get('dmg_mult', 1.0)}x power)."
            if t == 'heal_and_damage':
                return f"Heals {int(effect.get('heal_pct', 0)*100)}% of your max HP and deals damage ({effect.get('dmg_mult', 1.0)}x power)."
            if t == 'shield':
                return f"Grants a shield absorbing {int(effect.get('shield_pct', 0)*100)}% of your max HP in damage for {effect.get('duration', 1)} turn(s)."
            if t == 'pierce_damage':
                return f"Deals piercing damage ({effect.get('dmg_mult', 1.0)}x power), ignoring {int(effect.get('def_ignore_pct', 0)*100)}% of enemy DEF."
            return "Deals damage."

        embed = discord.Embed(title=f"⚔️ {member.name}'s Skills — {race}", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)

        for i, skill in enumerate(race_skills['skills']):
            current_name = get_skill_name(race, i, level)
            current_effect = get_skill_effect(race, i, level)
            effect_text = describe_effect(current_effect)
            next_evo = None
            for j, evo_level in enumerate(skill['evo_levels']):
                if level < evo_level:
                    next_evo = f"\nEvolves at level `{evo_level}` → **{skill['evolutions'][j]}**"
                    break
            embed.add_field(
                name=f"Skill {i+1} — **{current_name}**",
                value=f"{effect_text}{next_evo if next_evo else chr(10) + '✅ Max Evolution!'}",
                inline=False)

        if level >= special['unlock_level']:
            embed.add_field(
                name=f"💫 Special — **{special['name']}**",
                value="✅ Unlocked! Use in battle after 2 skill uses.",
                inline=False)
        else:
            embed.add_field(
                name="💫 Special — ???",
                value=f"🔒 Unlocks at level `{special['unlock_level']}`",
                inline=False)

        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="assign")
    async def assign(self, ctx, stat: str = None, amount: int = None):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return

        p = p[0]
        valid_stats = ['hp', 'str', 'mag', 'def']

        if not stat or stat.lower() not in valid_stats:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!assign <stat> <amount>`\nValid: `hp`, `str`, `mag`, `def`",
                color=GOLD))
            return

        if not amount or amount <= 0:
            await ctx.send(embed=discord.Embed(description="❌ Enter a valid amount!", color=GOLD))
            return

        unspent = p.get('unspent_points', 0)
        if amount > unspent:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Only `{unspent}` unspent points!",
                color=GOLD))
            return

        stat = stat.lower()
        new_stat = p.get(stat, 0) + amount
        players.update({stat: new_stat, 'unspent_points': unspent - amount}, Player.id == user_id)

        embed = discord.Embed(title="✅ Stats Assigned!", color=GOLD)
        embed.add_field(name=f"Added to {stat.upper()}", value=f"`+{amount}` → `{new_stat:,}`", inline=False)
        embed.add_field(name="Remaining Points", value=f"`{unspent - amount}`", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx, category: str = "level"):
        valid = ["level", "coins", "starshards", "guildrank"]
        if category not in valid:
            category = "level"
        view = LbView(ctx, category)
        await ctx.send(embed=view.build_embed(), view=view)

    @commands.command(name="rank")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        user_id = str(member.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Player not found!", color=GOLD))
            return

        p = p[0]
        all_players = players.all()
        sorted_p = sorted(all_players, key=lambda x: x.get('level', 1), reverse=True)
        rank_pos = next((i+1 for i, pl in enumerate(sorted_p) if pl['id'] == user_id), None)

        embed = discord.Embed(title=f"🏆 {member.name}'s Rank", color=GOLD)
        embed.add_field(name="Level Rank", value=f"`#{rank_pos}` / `{len(all_players)}`", inline=False)
        embed.add_field(name="Level", value=f"`{p.get('level', 1):,}`", inline=True)
        embed.add_field(name="EXP", value=f"`{p.get('exp', 0):,}`", inline=True)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="race", aliases=["races"])
    async def race(self, ctx):
        from main import RACES as RACE_DATA
        embed = discord.Embed(
            title="🌍 Nexworld Races",
            description="All races and their chances on `!start`",
            color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)

        chances = {
            "Human": "30%", "Halfblood": "25%", "Kobold": "25%",
            "Elf": "10%", "Beastkin": "7%", "Dragon-kin": "2%", "Seraphim": "1%"
        }

        for race_name, data in RACE_DATA.items():
            embed.add_field(
                name=f"{data['rarity_icon']} {race_name} — `{data['rarity']}` ({chances.get(race_name, '?')})",
                value=f"❤️ HP: `{data['hp']}` • ⚔️ STR: `{data['str']}` • ✨ MAG: `{data['mag']}` • 🛡️ DEF: `{data['def']}`",
                inline=False)

        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="💡 Notes",
            value="🔄 Reincarnation → Rare/Primordial only!\n⚡ Teleported → Higher Primordial chance!",
            inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help(self, ctx):
        embed = discord.Embed(title="📖 Nexworld RPG — Commands", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="🌟 Starting",
            value="`!start` • `!daily` • `!hourly` / `!hr` • `!explore` / `!e` • `!vote` • `!race` / `!races`",
            inline=False)
        embed.add_field(name="👤 Profile",
            value="`!profile` / `!pf` • `!balance` / `!bal` • `!inventory` / `!inv` *(paginated, ◀▶)* • `!skills` • `!points` • `!assign <stat> <amt>` • `!rank` • `!leaderboard` / `!lb [level|coins|starshards]` *(paginated)* • `!equipped`",
            inline=False)
        embed.add_field(name="⚔️ Battle",
            value="`!arc` • `!arc <number>` • `!battle <number>` / `!b <number>`\n*(You can only fight one battle at a time)*",
            inline=False)
        embed.add_field(name="🥊 PvP",
            value="`!fight @user` — Challenge another player to a duel!\nWinner earns `2,000–5,000` Nexcoins.",
            inline=False)
        embed.add_field(name="👹 Raids",
            value="`!raid` — Spawns a boss (costs 1x Raid Pass)\n`!raid <id>` — View a specific boss info",
            inline=False)
        embed.add_field(name="🏛️ Adventurer's Guild",
            value="`!guild` — Guild rank & info\n`!guild board` — View quest board\n`!accept <ID>` — Accept a quest\n`!report <ID>` — Report quest\n`!abandon <ID>` — Abandon quest\n`!myquests` / `!mq` — View active quests\n`!rankup` — Rank up\n`!gather` — Collect herbs (5-min CD, quest only)\n`!travel` — Delivery mission with encounter",
            inline=False)
        embed.add_field(name="🏰 Clans",
            value="`!clan register <name>` — Create (50,000 NC)\n`!clan join <name>` / `!cj <name>` — Join clan\n`!clan info <name>` / `!ci <name>` — View clan\n`!clans` — Clan leaderboard\n`!clan invite @user` • `!clan kick @user`\n`!clan deposit <amt>` • `!clan setdesc <text>`\n`!clan shop` / `!cs` — Clan shop\n`!inviteonly` / `!io` — Toggle invite-only",
            inline=False)
        embed.add_field(name="🎒 Items",
            value="`!ie <id>` Equip • `!iue <slot>` Unequip • `!usebuff <id>` Use Buff\n`!sell <id>` Sell (materials/drops/raid drops) • `!equipped`",
            inline=False)
        embed.add_field(name="💰 Economy",
            value="`!pay @user <amt>` • `!payss @user <amt>`\n*(Shortcuts: `10k` = 10,000 • `1m` = 1,000,000)*\n`!market` / `!m` • `!ma <id> <price>` List • `!mb <listing-id>` Buy • `!mr <listing-id>` Remove\n`!rebirth` • `!cd`",
            inline=False)
        embed.add_field(name="🛒 Shop",
            value="`!shop` — Main menu\n`!shop 1` — Nexcoin Shop *(paginated, ◀▶)*\n`!shop 2` — Starshard Shop\n`!buy 1 <item id>` • `!buy 2 <item id>` • `!buy daily <1-5>`",
            inline=False)
        embed.add_field(name="⚙️ Settings",
            value="`!setprefix <symbol>` — Allowed: `! $ - * ? .`",
            inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Profile(bot))