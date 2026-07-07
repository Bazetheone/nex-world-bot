import discord
from discord.ext import commands
from tinydb import TinyDB, Query
from db import players, Player
import random
import time
import asyncio

GOLD = 0xFFD700
ADMIN_IDS = ["954487623462813757"]

clan_db = TinyDB('clan_data.json')
ClanQ = Query()

CLAN_CREATE_COST = 50000
DEFAULT_MAX_MEMBERS = 3
MEMBER_EXPANDER_COST = 1000
MIN_REP_FOR_SEASON_REWARD = 1000

SEASON_REWARDS = [
    {"nc": 500000, "exp": 50000, "cc": 10000, "rarity": "Legendary"},
    {"nc": 400000, "exp": 40000, "cc": 8000,  "rarity": "Legendary"},
    {"nc": 300000, "exp": 30000, "cc": 6000,  "rarity": "Epic"},
    {"nc": 225000, "exp": 22500, "cc": 4500,  "rarity": "Epic"},
    {"nc": 175000, "exp": 17500, "cc": 3500,  "rarity": "Rare"},
    {"nc": 140000, "exp": 14000, "cc": 2800,  "rarity": "Rare"},
    {"nc": 110000, "exp": 11000, "cc": 2200,  "rarity": "Rare"},
    {"nc": 85000,  "exp": 8500,  "cc": 1700,  "rarity": "Uncommon"},
    {"nc": 65000,  "exp": 6500,  "cc": 1300,  "rarity": "Uncommon"},
    {"nc": 50000,  "exp": 5000,  "cc": 1000,  "rarity": "Uncommon"},
]

SEASON_ITEMS = {
    "Legendary": [
        {"name": "Mythbreaker's Edge", "stats": {"str": 300, "hp": 200}, "type": "weapon", "description": "Season reward — +300 STR, +200 HP"},
        {"name": "Void Sovereign's Cloak", "stats": {"def": 350, "hp": 250}, "type": "armor", "description": "Season reward — +350 DEF, +250 HP"},
    ],
    "Epic": [
        {"name": "Champion's Greatsword", "stats": {"str": 180}, "type": "weapon", "description": "Season reward — +180 STR"},
        {"name": "Champion's Bulwark", "stats": {"def": 200, "hp": 150}, "type": "armor", "description": "Season reward — +200 DEF, +150 HP"},
    ],
    "Rare": [
        {"name": "Season Blade", "stats": {"str": 80}, "type": "weapon", "description": "Season reward — +80 STR"},
        {"name": "Season Shield", "stats": {"def": 90}, "type": "armor", "description": "Season reward — +90 DEF"},
    ],
    "Uncommon": [
        {"name": "Season Dagger", "stats": {"str": 35}, "type": "weapon", "description": "Season reward — +35 STR"},
        {"name": "Season Vest", "stats": {"def": 40}, "type": "armor", "description": "Season reward — +40 DEF"},
    ],
}

current_season = [1]


def get_player_clan(user_id):
    results = clan_db.search(ClanQ.members.any([user_id]))
    return results[0] if results else None


def get_sorted_clans():
    all_clans = clan_db.all()
    return sorted(all_clans, key=lambda c: c.get('total_rep', 0), reverse=True)


class ClansLeaderboardView(discord.ui.View):
    def __init__(self, ctx, page=1):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.page = page
        self.per_page = 10

    def build_embed(self):
        all_clans = get_sorted_clans()
        total = len(all_clans)
        total_pages = max(1, (total + self.per_page - 1) // self.per_page)
        self.page = max(1, min(self.page, total_pages))
        start = (self.page - 1) * self.per_page
        page_clans = all_clans[start:start + self.per_page]
        medals = ["🥇", "🥈", "🥉"]
        embed = discord.Embed(title=f"🏆 Clan Leaderboard — Season {current_season[0]}", color=GOLD)
        embed.description = f"Ranked by total reputation earned this season.\n"
        for i, c in enumerate(page_clans):
            global_rank = start + i + 1
            icon = medals[global_rank - 1] if global_rank <= 3 else f"`#{global_rank}`"
            lock = "🔒" if c.get('invite_only', False) else ""
            embed.add_field(
                name=f"{icon} {c['name']} {lock}",
                value=(f"👑 Leader: **{c.get('owner_name', '?')}** | "
                       f"👥 `{len(c['members'])}/{c.get('max_members', DEFAULT_MAX_MEMBERS)}` | "
                       f"⭐ `{c.get('total_rep', 0):,}` Rep"),
                inline=False)
        embed.set_footer(text=f"Page {self.page}/{total_pages} • Nexworld RPG")
        return embed, total_pages

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.grey)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        self.page = max(1, self.page - 1)
        embed, _ = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.grey)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        _, total_pages = self.build_embed()
        self.page = min(total_pages, self.page + 1)
        embed, _ = self.build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.red)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your leaderboard!", ephemeral=True)
            return
        await interaction.response.edit_message(embed=discord.Embed(description="🏆 Leaderboard closed.", color=GOLD), view=None)
        self.stop()


class Clan(commands.Cog, name="Clan"):
    def __init__(self, bot):
        self.bot = bot

    def _get_clan_embed(self, c):
        members = c.get('members', [])
        max_m = c.get('max_members', DEFAULT_MAX_MEMBERS)
        leaders = c.get('officers', [])
        lock = "🔒 Invite Only" if c.get('invite_only', False) else "🔓 Open"
        embed = discord.Embed(title=f"🏰 Clan: {c['name']}", color=GOLD)
        embed.description = c.get('description', '*No description set.*')
        embed.add_field(name="👑 Leader", value=f"**{c.get('owner_name', '?')}**", inline=True)
        embed.add_field(name="👥 Members", value=f"`{len(members)}/{max_m}`", inline=True)
        embed.add_field(name="🔑 Status", value=lock, inline=True)
        embed.add_field(name="⭐ Season Rep", value=f"`{c.get('total_rep', 0):,}`", inline=True)
        embed.add_field(name="💰 Treasury", value=f"`{c.get('treasury', 0):,}` NC", inline=True)
        embed.add_field(name="🪙 Clan Coins", value=f"`{c.get('clan_coins', 0):,}` CC", inline=True)
        if c.get('officers'):
            embed.add_field(name="🛡️ Officers", value=", ".join(c['officers'][:5]) or "None", inline=False)
        member_names = c.get('member_names', members)
        embed.add_field(name="📋 Members", value=", ".join(member_names[:12]) + (f" +{len(members)-12} more" if len(members) > 12 else "") or "None", inline=False)
        clan_rank_list = get_sorted_clans()
        pos = next((i+1 for i, cl in enumerate(clan_rank_list) if cl['name'] == c['name']), '?')
        embed.add_field(name="🏆 Leaderboard Position", value=f"`#{pos}`", inline=True)
        embed.set_footer(text=f"Season {current_season[0]} • Nexworld RPG")
        return embed

    @commands.group(name="clan", invoke_without_command=True)
    async def clan_cmd(self, ctx):
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if c:
            await ctx.send(embed=self._get_clan_embed(c))
        else:
            embed = discord.Embed(title="🏰 Clan Commands", color=GOLD)
            embed.description = (
                "`!clan register <name>` — Create a clan (`50,000` NC)\n"
                "`!clan join <name>` / `!cj <name>` — Join a clan\n"
                "`!clan info <name>` / `!ci <name>` — View clan info\n"
                "`!clan invite @user` — Invite a player\n"
                "`!clan kick @user` — Kick a member\n"
                "`!clan promote @user` — Promote to officer\n"
                "`!clan deposit <amount>` — Donate NC to treasury\n"
                "`!clan setdesc <text>` — Set clan description\n"
                "`!clan leave` — Leave your clan\n"
                "`!clan shop` / `!cs` — Clan shop\n"
                "`!clans` — Clan leaderboard\n"
                "`!inviteonly` / `!io` — Toggle invite-only"
            )
            embed.set_footer(text="Nexworld RPG • Clan System")
            await ctx.send(embed=embed)

    @clan_cmd.command(name="register")
    async def clan_register(self, ctx, *, name: str = None):
        if not name:
            await ctx.send(embed=discord.Embed(description="Usage: `!clan register <name>`", color=GOLD))
            return
        if len(name) > 32:
            await ctx.send(embed=discord.Embed(description="❌ Clan name must be 32 characters or less!", color=GOLD))
            return
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        p = p[0]
        if get_player_clan(user_id):
            await ctx.send(embed=discord.Embed(description="❌ You are already in a clan! Leave it first.", color=GOLD))
            return
        if clan_db.search(ClanQ.name == name):
            await ctx.send(embed=discord.Embed(description=f"❌ A clan named **{name}** already exists!", color=GOLD))
            return
        if p.get('nexcoins', 0) < CLAN_CREATE_COST:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Need `{CLAN_CREATE_COST:,}` NC! You have `{p['nexcoins']:,}`", color=GOLD))
            return
        players.update({'nexcoins': p['nexcoins'] - CLAN_CREATE_COST}, Player.id == user_id)
        clan_db.insert({
            'name': name,
            'owner_id': user_id,
            'owner_name': ctx.author.display_name,
            'members': [user_id],
            'member_names': [ctx.author.display_name],
            'officers': [],
            'invites': [],
            'max_members': DEFAULT_MAX_MEMBERS,
            'treasury': 0,
            'clan_coins': 0,
            'total_rep': 0,
            'description': f'Welcome to {name}!',
            'invite_only': False,
            'created_at': int(time.time()),
            'season': current_season[0],
        })
        embed = discord.Embed(title=f"🏰 Clan Created: {name}!", color=GOLD)
        embed.description = f"Cost: `{CLAN_CREATE_COST:,}` NC deducted.\nMax members: `{DEFAULT_MAX_MEMBERS}` (expand via `!clan shop`)"
        embed.set_footer(text="Nexworld RPG • Clan System")
        await ctx.send(embed=embed)

    @clan_cmd.command(name="info")
    async def clan_info(self, ctx, *, name: str = None):
        if name:
            results = clan_db.search(ClanQ.name == name)
            if not results:
                await ctx.send(embed=discord.Embed(description=f"❌ Clan **{name}** not found!", color=GOLD))
                return
            c = results[0]
        else:
            user_id = str(ctx.author.id)
            c = get_player_clan(user_id)
            if not c:
                await ctx.send(embed=discord.Embed(description="❌ You're not in a clan! Use `!clan info <name>`", color=GOLD))
                return
        await ctx.send(embed=self._get_clan_embed(c))

    @clan_cmd.command(name="join")
    async def clan_join(self, ctx, *, name: str = None):
        if not name:
            await ctx.send(embed=discord.Embed(description="Usage: `!clan join <name>`", color=GOLD))
            return
        user_id = str(ctx.author.id)
        if get_player_clan(user_id):
            await ctx.send(embed=discord.Embed(description="❌ You're already in a clan! Leave first.", color=GOLD))
            return
        results = clan_db.search(ClanQ.name == name)
        if not results:
            await ctx.send(embed=discord.Embed(description=f"❌ Clan **{name}** not found!", color=GOLD))
            return
        c = results[0]
        if c.get('invite_only', False) and user_id not in c.get('invites', []):
            await ctx.send(embed=discord.Embed(description="❌ This clan is invite-only! Ask the leader for an invite.", color=GOLD))
            return
        if len(c['members']) >= c.get('max_members', DEFAULT_MAX_MEMBERS):
            await ctx.send(embed=discord.Embed(description="❌ This clan is full!", color=GOLD))
            return
        members = c['members'] + [user_id]
        member_names = c.get('member_names', []) + [ctx.author.display_name]
        invites = [i for i in c.get('invites', []) if i != user_id]
        clan_db.update({'members': members, 'member_names': member_names, 'invites': invites}, ClanQ.name == name)
        await ctx.send(embed=discord.Embed(
            title="🏰 Joined Clan!",
            description=f"Welcome to **{name}**, {ctx.author.mention}!",
            color=GOLD))

    @clan_cmd.command(name="leave")
    async def clan_leave(self, ctx):
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if not c:
            await ctx.send(embed=discord.Embed(description="❌ You're not in a clan!", color=GOLD))
            return
        if c['owner_id'] == user_id:
            await ctx.send(embed=discord.Embed(description="❌ You're the leader! Use `!clan disband` first.", color=GOLD))
            return
        members = [m for m in c['members'] if m != user_id]
        member_names = [n for n in c.get('member_names', []) if n != ctx.author.display_name]
        officers = [o for o in c.get('officers', []) if o != user_id]
        clan_db.update({'members': members, 'member_names': member_names, 'officers': officers}, ClanQ.name == c['name'])
        await ctx.send(embed=discord.Embed(description=f"👋 You left **{c['name']}**.", color=GOLD))

    @clan_cmd.command(name="invite")
    async def clan_invite(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send(embed=discord.Embed(description="Usage: `!clan invite @user`", color=GOLD))
            return
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if not c:
            await ctx.send(embed=discord.Embed(description="❌ You're not in a clan!", color=GOLD))
            return
        if c['owner_id'] != user_id and user_id not in c.get('officers', []):
            await ctx.send(embed=discord.Embed(description="❌ Only the leader or officers can invite!", color=GOLD))
            return
        target_id = str(member.id)
        if target_id in c['members']:
            await ctx.send(embed=discord.Embed(description="❌ That player is already in the clan!", color=GOLD))
            return
        if get_player_clan(target_id):
            await ctx.send(embed=discord.Embed(description="❌ That player is already in another clan!", color=GOLD))
            return
        if len(c['members']) >= c.get('max_members', DEFAULT_MAX_MEMBERS):
            await ctx.send(embed=discord.Embed(description="❌ Clan is full! Buy a Member Expander from `!clan shop`", color=GOLD))
            return
        invites = c.get('invites', [])
        if target_id not in invites:
            invites.append(target_id)
            clan_db.update({'invites': invites}, ClanQ.name == c['name'])
        embed = discord.Embed(title="📨 Clan Invite Sent!", color=GOLD)
        embed.description = f"{member.mention}, you've been invited to join **{c['name']}**!\nUse `!clan join {c['name']}` to accept."
        await ctx.send(embed=embed)

    @clan_cmd.command(name="kick")
    async def clan_kick(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send(embed=discord.Embed(description="Usage: `!clan kick @user`", color=GOLD))
            return
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if not c:
            await ctx.send(embed=discord.Embed(description="❌ You're not in a clan!", color=GOLD))
            return
        if c['owner_id'] != user_id and user_id not in c.get('officers', []):
            await ctx.send(embed=discord.Embed(description="❌ Only the leader or officers can kick!", color=GOLD))
            return
        target_id = str(member.id)
        if target_id not in c['members']:
            await ctx.send(embed=discord.Embed(description="❌ That player is not in your clan!", color=GOLD))
            return
        if target_id == c['owner_id']:
            await ctx.send(embed=discord.Embed(description="❌ Cannot kick the clan leader!", color=GOLD))
            return
        members = [m for m in c['members'] if m != target_id]
        member_names = [n for n in c.get('member_names', []) if n != member.display_name]
        officers = [o for o in c.get('officers', []) if o != target_id]
        clan_db.update({'members': members, 'member_names': member_names, 'officers': officers}, ClanQ.name == c['name'])
        await ctx.send(embed=discord.Embed(
            description=f"🦵 **{member.display_name}** was kicked from **{c['name']}**.", color=GOLD))

    @clan_cmd.command(name="promote")
    async def clan_promote(self, ctx, member: discord.Member = None):
        if not member:
            await ctx.send(embed=discord.Embed(description="Usage: `!clan promote @user`", color=GOLD))
            return
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if not c or c['owner_id'] != user_id:
            await ctx.send(embed=discord.Embed(description="❌ Only the clan leader can promote!", color=GOLD))
            return
        target_id = str(member.id)
        if target_id not in c['members']:
            await ctx.send(embed=discord.Embed(description="❌ That player is not in your clan!", color=GOLD))
            return
        officers = c.get('officers', [])
        if target_id in officers:
            await ctx.send(embed=discord.Embed(description=f"❌ **{member.display_name}** is already an officer!", color=GOLD))
            return
        officers.append(target_id)
        officer_names = c.get('officer_names', []) + [member.display_name]
        clan_db.update({'officers': officers, 'officer_names': officer_names}, ClanQ.name == c['name'])
        await ctx.send(embed=discord.Embed(
            description=f"⭐ **{member.display_name}** promoted to Officer of **{c['name']}**!", color=GOLD))

    @clan_cmd.command(name="deposit")
    async def clan_deposit(self, ctx, amount: int = None):
        if not amount or amount <= 0:
            await ctx.send(embed=discord.Embed(description="Usage: `!clan deposit <amount>`", color=GOLD))
            return
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        p = p[0]
        c = get_player_clan(user_id)
        if not c:
            await ctx.send(embed=discord.Embed(description="❌ You're not in a clan!", color=GOLD))
            return
        if p.get('nexcoins', 0) < amount:
            await ctx.send(embed=discord.Embed(description=f"❌ Not enough NC! You have `{p['nexcoins']:,}`", color=GOLD))
            return
        players.update({'nexcoins': p['nexcoins'] - amount}, Player.id == user_id)
        new_treasury = c.get('treasury', 0) + amount
        clan_db.update({'treasury': new_treasury}, ClanQ.name == c['name'])
        embed = discord.Embed(title="💰 Deposit Successful!", color=GOLD)
        embed.add_field(name="Donated", value=f"`{amount:,}` NC", inline=True)
        embed.add_field(name="Treasury", value=f"`{new_treasury:,}` NC", inline=True)
        await ctx.send(embed=embed)

    @clan_cmd.command(name="setdesc")
    async def clan_setdesc(self, ctx, *, desc: str = None):
        if not desc:
            await ctx.send(embed=discord.Embed(description="Usage: `!clan setdesc <text>`", color=GOLD))
            return
        if len(desc) > 100:
            await ctx.send(embed=discord.Embed(description="❌ Description max 100 chars!", color=GOLD))
            return
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if not c or c['owner_id'] != user_id:
            await ctx.send(embed=discord.Embed(description="❌ Only the clan leader can set the description!", color=GOLD))
            return
        clan_db.update({'description': desc}, ClanQ.name == c['name'])
        await ctx.send(embed=discord.Embed(description="✅ Clan description updated!", color=GOLD))

    @clan_cmd.command(name="disband")
    async def clan_disband(self, ctx):
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if not c or c['owner_id'] != user_id:
            await ctx.send(embed=discord.Embed(description="❌ Only the clan leader can disband!", color=GOLD))
            return
        clan_db.remove(ClanQ.name == c['name'])
        await ctx.send(embed=discord.Embed(description=f"💀 **{c['name']}** has been disbanded.", color=GOLD))

    @clan_cmd.command(name="shop")
    async def clan_shop(self, ctx):
        embed = discord.Embed(title="🛒 Clan Shop", color=GOLD)
        embed.add_field(
            name=f"1️⃣ Member Expander — `{MEMBER_EXPANDER_COST:,}` Clan Coins",
            value="Permanently increases your clan's max member slots by **+1**.\nClan starts at 3 slots — every purchase unlocks one more seat.",
            inline=False)
        embed.set_footer(text="Use !cs buy 1 to purchase • Nexworld RPG")
        await ctx.send(embed=embed)

    @commands.command(name="cs")
    async def cs_shortcut(self, ctx, action: str = None, item_id: int = None):
        if not action:
            await self.clan_shop(ctx)
            return
        if action.lower() == "buy":
            await self.clan_shop_buy(ctx, item_id)
        else:
            await ctx.send(embed=discord.Embed(description="Usage: `!cs buy <item_id>`", color=GOLD))

    async def clan_shop_buy(self, ctx, item_id):
        if item_id != 1:
            await ctx.send(embed=discord.Embed(description="❌ Invalid item ID! Check `!clan shop` for available items.", color=GOLD))
            return
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        p = p[0]
        c = get_player_clan(user_id)
        if not c or c['owner_id'] != user_id:
            await ctx.send(embed=discord.Embed(description="❌ Only clan leaders can buy from the clan shop!", color=GOLD))
            return
        cc = p.get('clan_coins', 0)
        if cc < MEMBER_EXPANDER_COST:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Not enough Clan Coins! Need `{MEMBER_EXPANDER_COST}` CC • You have `{cc}`", color=GOLD))
            return
        players.update({'clan_coins': cc - MEMBER_EXPANDER_COST}, Player.id == user_id)
        new_max = c.get('max_members', DEFAULT_MAX_MEMBERS) + 1
        clan_db.update({'max_members': new_max}, ClanQ.name == c['name'])
        embed = discord.Embed(title="✅ Member Expander Purchased!", color=GOLD)
        embed.description = f"Clan **{c['name']}** can now hold **{new_max}** members!"
        await ctx.send(embed=embed)

    @commands.command(name="clans")
    async def clans_leaderboard(self, ctx):
        view = ClansLeaderboardView(ctx, 1)
        embed, _ = view.build_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="cj")
    async def cj(self, ctx, *, name: str = None):
        await self.clan_join(ctx, name=name)

    @commands.command(name="ci")
    async def ci(self, ctx, *, name: str = None):
        await self.clan_info(ctx, name=name)

    @commands.command(name="inviteonly", aliases=["io"])
    async def invite_only(self, ctx):
        user_id = str(ctx.author.id)
        c = get_player_clan(user_id)
        if not c or c['owner_id'] != user_id:
            await ctx.send(embed=discord.Embed(description="❌ Only the clan leader can change this!", color=GOLD))
            return
        new_val = not c.get('invite_only', False)
        clan_db.update({'invite_only': new_val}, ClanQ.name == c['name'])
        state = "🔒 **Invite Only**" if new_val else "🔓 **Open to All**"
        await ctx.send(embed=discord.Embed(description=f"✅ Clan is now {state}", color=GOLD))

    @commands.command(name="admin", pass_context=True)
    async def admin_cmd(self, ctx, sub: str = None, *, args: str = None):
        user_id = str(ctx.author.id)
        if user_id not in ADMIN_IDS:
            await ctx.send(embed=discord.Embed(description="❌ Admin only!", color=GOLD))
            return
        if not sub:
            embed = discord.Embed(title="🔧 Admin Commands", color=GOLD)
            embed.add_field(name="💰 Economy", value="`!admin give <@user> <amount>` — Give NC\n`!admin givess <@user> <amount>` — Give SS\n`!admin ban <@user> [minutes]` — Ban player\n`!admin unban <@user>` — Unban player\n`!admin setlevel <@user> <level>` — Set level\n`!admin wipe <@user>` — Wipe player data", inline=False)
            embed.add_field(name="🏆 Season Management", value="`!admin resetrep` — Reset all player guild rep\n`!admin resetclanrep` — Reset all clan reputation\n`!admin endseason` — End season & distribute rewards\n`!admin setseason <number>` — Set season number", inline=False)
            embed.set_footer(text="Nexworld RPG • Admin Panel")
            await ctx.send(embed=embed)
            return

        sub = sub.lower()

        if sub == "resetrep":
            all_p = players.all()
            for p in all_p:
                players.update({'guild_rep': 0, 'guild_rank': 'F', 'active_quests': [], 'quest_board': [], 'quest_board_refreshed': 0}, Player.id == p['id'])
            await ctx.send(embed=discord.Embed(title="🔄 Rep Reset", description=f"All `{len(all_p)}` players' guild reputation, rank, and quests reset to F-Rank.", color=GOLD))

        elif sub == "resetclanrep":
            all_clans = clan_db.all()
            for c in all_clans:
                clan_db.update({'total_rep': 0}, ClanQ.name == c['name'])
            await ctx.send(embed=discord.Embed(title="🔄 Clan Rep Reset", description=f"All `{len(all_clans)}` clan reputation scores reset to 0.", color=GOLD))

        elif sub == "setseason":
            if not args or not args.strip().isdigit():
                await ctx.send(embed=discord.Embed(description="Usage: `!admin setseason <number>`", color=GOLD))
                return
            current_season[0] = int(args.strip())
            await ctx.send(embed=discord.Embed(description=f"✅ Season set to **{current_season[0]}**.", color=GOLD))

        elif sub == "endseason":
            sorted_clans = get_sorted_clans()
            top10 = sorted_clans[:10]
            if not top10:
                await ctx.send(embed=discord.Embed(description="❌ No clans to reward!", color=GOLD))
                return

            recap_embed = discord.Embed(
                title=f"🏆 Season {current_season[0]} — End of Season Results!",
                description="The season has ended! Congratulations to all top clans!",
                color=0xFFD700)
            medals = ["🥇", "🥈", "🥉"]

            for place, c in enumerate(top10):
                reward = SEASON_REWARDS[place]
                icon = medals[place] if place < 3 else f"#{place+1}"
                recap_embed.add_field(
                    name=f"{icon} {c['name']}",
                    value=f"⭐ `{c.get('total_rep', 0):,}` Rep | 💰 `{reward['nc']:,}` NC | ✨ {reward['rarity']} Item",
                    inline=False)

                for member_id in c.get('members', []):
                    mp = players.search(Player.id == member_id)
                    if not mp:
                        continue
                    mp = mp[0]
                    if mp.get('guild_rep', 0) < MIN_REP_FOR_SEASON_REWARD:
                        continue
                    season_item_pool = SEASON_ITEMS.get(reward['rarity'], [])
                    chosen_item = random.choice(season_item_pool) if season_item_pool else None
                    updates = {
                        'nexcoins': mp.get('nexcoins', 0) + reward['nc'],
                        'exp': mp.get('exp', 0) + reward['exp'],
                        'clan_coins': mp.get('clan_coins', 0) + reward['cc'],
                    }
                    if chosen_item:
                        inv = mp.get('inventory', [])
                        import random as _random
                        uid = str(_random.randint(100000, 999999))
                        inv.append({
                            'uid': uid,
                            'name': chosen_item['name'],
                            'rarity': reward['rarity'],
                            'type': chosen_item['type'],
                            'description': chosen_item['description'],
                            'stats': chosen_item['stats'],
                        })
                        updates['inventory'] = inv
                    players.update(updates, Player.id == member_id)
                    try:
                        user = self.bot.get_user(int(member_id))
                        if user:
                            dm_embed = discord.Embed(
                                title=f"🏆 Season {current_season[0]} Reward!",
                                description=f"Your clan **{c['name']}** finished **{icon}**!",
                                color=0xFFD700)
                            dm_embed.add_field(name="💰 Nexcoins", value=f"`+{reward['nc']:,}`", inline=True)
                            dm_embed.add_field(name="⭐ EXP", value=f"`+{reward['exp']:,}`", inline=True)
                            dm_embed.add_field(name="🪙 Clan Coins", value=f"`+{reward['cc']:,}`", inline=True)
                            if chosen_item:
                                dm_embed.add_field(name=f"🎁 Item ({reward['rarity']})", value=f"**{chosen_item['name']}**", inline=False)
                            await user.send(embed=dm_embed)
                    except:
                        pass

            current_season[0] += 1
            all_p = players.all()
            for p in all_p:
                players.update({'guild_rep': 0, 'guild_rank': 'F', 'active_quests': [], 'quest_board': [], 'quest_board_refreshed': 0}, Player.id == p['id'])
            for c in clan_db.all():
                clan_db.update({'total_rep': 0, 'season': current_season[0]}, ClanQ.name == c['name'])

            recap_embed.set_footer(text=f"Season {current_season[0]} has begun! Nexworld RPG")
            await ctx.send(embed=recap_embed)

        else:
            await ctx.send(embed=discord.Embed(description=f"❌ Unknown admin subcommand: `{sub}`", color=GOLD))


async def setup(bot):
    await bot.add_cog(Clan(bot))
