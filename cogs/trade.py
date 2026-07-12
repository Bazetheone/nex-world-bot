import discord
from discord.ext import commands
from db import players, Player

GOLD = 0xFFD700

CATEGORY_TYPES = {
    "Weapon": ["weapon"],
    "Armor": ["armor", "head_armor", "body_armor"],
    "Pet": ["pet"],
    "Material": ["material", "consumable", "buff", "drop", "admin_given", "raid_drop", "returned", "purchased"],
}

def get_equipped_uids(p):
    eq = p.get('equipped', {})
    return {v['uid'] for v in eq.values() if v and isinstance(v, dict) and 'uid' in v}

class TradeSession:
    def __init__(self, user_a: discord.Member, user_b: discord.Member):
        self.user_a = user_a
        self.user_b = user_b
        self.offers = {str(user_a.id): [], str(user_b.id): []}
        self.confirmed = {str(user_a.id): False, str(user_b.id): False}
        self.message = None
        self.cancelled = False

    def other(self, user_id):
        ids = list(self.offers.keys())
        return ids[0] if ids[1] == user_id else ids[1]

class ItemSelect(discord.ui.Select):
    def __init__(self, session: TradeSession, user_id: str, items):
        self.session = session
        self.user_id = user_id
        options = [
            discord.SelectOption(
                label=f"{i['name']} ({i.get('rarity','?')})"[:100],
                value=i['uid']
            ) for i in items[:25]
        ]
        super().__init__(placeholder="Select item(s) to offer", min_values=1, max_values=len(options), options=options)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Not your selection!", ephemeral=True)
            return
        for uid in self.values:
            if uid not in self.session.offers[self.user_id]:
                self.session.offers[self.user_id].append(uid)
        self.session.confirmed[self.session.user_a.id.__str__()] = False
        self.session.confirmed[self.session.user_b.id.__str__()] = False
        await interaction.response.edit_message(content="✅ Added to your offer!", view=None)
        await self.session.message.edit(embed=build_trade_embed(self.session))

class CategoryPickView(discord.ui.View):
    def __init__(self, session: TradeSession, user_id: str, items):
        super().__init__(timeout=60)
        if items:
            self.add_item(ItemSelect(session, user_id, items))

def build_trade_embed(session: TradeSession):
    embed = discord.Embed(title="🔄 Trade!", color=GOLD)
    for uid_str, member in [(str(session.user_a.id), session.user_a), (str(session.user_b.id), session.user_b)]:
        p = players.search(Player.id == uid_str)
        inv = {i['uid']: i for i in p[0].get('inventory', [])} if p else {}
        lines = []
        for offered_uid in session.offers[uid_str]:
            item = inv.get(offered_uid)
            if item:
                lines.append(f"• {item['name']} ({item.get('rarity','?')})")
        status = "✅ Confirmed" if session.confirmed.get(uid_str) else "⏳ Not confirmed"
        embed.add_field(
            name=f"{member.display_name} is offering:",
            value=("\n".join(lines) if lines else "*Nothing yet*") + f"\n\n{status}",
            inline=False)
    embed.set_footer(text="Both players must confirm to complete the trade • Nexworld RPG")
    return embed

class TradeView(discord.ui.View):
    def __init__(self, session: TradeSession):
        super().__init__(timeout=300)
        self.session = session

    def _get_eligible_items(self, user_id, category):
        p = players.search(Player.id == user_id)
        if not p:
            return []
        p = p[0]
        equipped_uids = get_equipped_uids(p)
        already_offered = set(self.session.offers[user_id])
        valid_types = CATEGORY_TYPES[category]
        return [
            i for i in p.get('inventory', [])
            if i.get('type') in valid_types
            and i.get('uid') not in equipped_uids
            and i.get('uid') not in already_offered
        ]

    async def _check_participant(self, interaction):
        uid = str(interaction.user.id)
        if uid not in self.session.offers:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return None
        return uid

    async def _add_category(self, interaction, category):
        uid = await self._check_participant(interaction)
        if not uid:
            return
        items = self._get_eligible_items(uid, category)
        if not items:
            await interaction.response.send_message(f"❌ You have no eligible {category} items to add!", ephemeral=True)
            return
        view = CategoryPickView(self.session, uid, items)
        await interaction.response.send_message(f"Pick {category} item(s) to offer:", view=view, ephemeral=True)

    @discord.ui.button(label="⚔️ Weapon", style=discord.ButtonStyle.blurple, row=0)
    async def add_weapon(self, interaction, button):
        await self._add_category(interaction, "Weapon")

    @discord.ui.button(label="🛡️ Armor", style=discord.ButtonStyle.blurple, row=0)
    async def add_armor(self, interaction, button):
        await self._add_category(interaction, "Armor")

    @discord.ui.button(label="🐾 Pet", style=discord.ButtonStyle.blurple, row=0)
    async def add_pet(self, interaction, button):
        await self._add_category(interaction, "Pet")

    @discord.ui.button(label="📦 Material", style=discord.ButtonStyle.blurple, row=0)
    async def add_material(self, interaction, button):
        await self._add_category(interaction, "Material")

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.green, row=1)
    async def confirm(self, interaction, button):
        uid = await self._check_participant(interaction)
        if not uid:
            return
        self.session.confirmed[uid] = True
        await interaction.response.edit_message(embed=build_trade_embed(self.session), view=self)

        if all(self.session.confirmed.values()):
            await self._execute_trade(interaction)

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red, row=1)
    async def cancel(self, interaction, button):
        uid = await self._check_participant(interaction)
        if not uid:
            return
        self.session.cancelled = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(
            embed=discord.Embed(description="❌ Trade cancelled.", color=GOLD), view=self)
        self.stop()

    async def _execute_trade(self, interaction):
        uid_a = str(self.session.user_a.id)
        uid_b = str(self.session.user_b.id)

        p_a = players.search(Player.id == uid_a)
        p_b = players.search(Player.id == uid_b)
        if not p_a or not p_b:
            await interaction.followup.send("❌ Trade failed — player data missing!")
            return
        p_a, p_b = p_a[0], p_b[0]

        inv_a = p_a.get('inventory', [])
        inv_b = p_b.get('inventory', [])
        inv_a_uids = {i['uid'] for i in inv_a}
        inv_b_uids = {i['uid'] for i in inv_b}

        offer_a = self.session.offers[uid_a]
        offer_b = self.session.offers[uid_b]

        if not all(u in inv_a_uids for u in offer_a) or not all(u in inv_b_uids for u in offer_b):
            for child in self.children:
                child.disabled = True
            await interaction.message.edit(
                embed=discord.Embed(description="❌ Trade failed — one or more items are no longer available!", color=0xFF0000),
                view=self)
            return

        items_from_a = [i for i in inv_a if i['uid'] in offer_a]
        items_from_b = [i for i in inv_b if i['uid'] in offer_b]

        new_inv_a = [i for i in inv_a if i['uid'] not in offer_a] + items_from_b
        new_inv_b = [i for i in inv_b if i['uid'] not in offer_b] + items_from_a

        players.update({'inventory': new_inv_a}, Player.id == uid_a)
        players.update({'inventory': new_inv_b}, Player.id == uid_b)

        for child in self.children:
            child.disabled = True
        embed = discord.Embed(title="✅ Trade Complete!", color=0x00FF00)
        embed.add_field(name=f"{self.session.user_a.display_name} received", value="\n".join(f"• {i['name']}" for i in items_from_b) or "Nothing", inline=False)
        embed.add_field(name=f"{self.session.user_b.display_name} received", value="\n".join(f"• {i['name']}" for i in items_from_a) or "Nothing", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await interaction.message.edit(embed=embed, view=self)
        self.stop()

class TradeInviteView(discord.ui.View):
    def __init__(self, inviter, target):
        super().__init__(timeout=60)
        self.inviter = inviter
        self.target = target
        self.accepted = None

    @discord.ui.button(label="✅ Yes", style=discord.ButtonStyle.green)
    async def yes(self, interaction, button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("This trade invite isn't for you!", ephemeral=True)
            return
        self.accepted = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="❌ No", style=discord.ButtonStyle.red)
    async def no(self, interaction, button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("This trade invite isn't for you!", ephemeral=True)
            return
        self.accepted = False
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

class Trade(commands.Cog, name="Trade"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="trade")
    async def trade(self, ctx, target: discord.Member = None):
        if not target:
            await ctx.send(embed=discord.Embed(description="Usage: `!trade @user`", color=GOLD))
            return
        if target.bot or target.id == ctx.author.id:
            await ctx.send(embed=discord.Embed(description="❌ Invalid trade target!", color=GOLD))
            return

        p1 = players.search(Player.id == str(ctx.author.id))
        p2 = players.search(Player.id == str(target.id))
        if not p1:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return
        if not p2:
            await ctx.send(embed=discord.Embed(description=f"❌ {target.name} hasn't started yet!", color=GOLD))
            return

        invite_view = TradeInviteView(ctx.author, target)
        invite_embed = discord.Embed(
            title="🔄 Trade Invite",
            description=f"{ctx.author.mention} has invited {target.mention} in a trade. Confirm or decline to continue.",
            color=GOLD)
        await ctx.send(embed=invite_embed, view=invite_view)
        await invite_view.wait()

        if not invite_view.accepted:
            await ctx.send(embed=discord.Embed(description="❌ Trade declined or timed out.", color=GOLD))
            return

        session = TradeSession(ctx.author, target)
        trade_view = TradeView(session)
        msg = await ctx.send(embed=build_trade_embed(session), view=trade_view)
        session.message = msg

async def setup(bot):
    await bot.add_cog(Trade(bot))
