import discord
from discord.ext import commands
from db import players, Player

GOLD = 0xFFD700
NEXITE_ICON = "<:nexite:1567658459342831636>"
MAX_UPGRADE_LEVEL = 5
FORGEABLE_TYPES = ('weapon', 'armor', 'head_armor', 'body_armor')

NEXITE_BASE_COST = {
    'Common': 2, 'Uncommon': 3, 'Rare': 5, 'Epic': 8, 'Legendary': 12,
    'Mythic': 15, 'Mythical': 15, 'Godly': 20, 'Divine': 25, 'Celestial': 30,
}

RARITY_ICONS = {
    "Common": "⚪", "Uncommon": "🟢", "Rare": "🔵", "Epic": "🟣",
    "Legendary": "🟠", "Mythic": "🔴", "Mythical": "🔴", "Divine": "🟡",
    "Celestial": "💠", "Godly": "🔱",
}


def forge_cost(item):
    base = NEXITE_BASE_COST.get(item.get('rarity', 'Common'), 5)
    return base * item.get('upgrade_level', 1)


def stat_label(stat):
    return "Magic Power" if stat == 'mag' else stat.upper()


def pct_at_level(item, race, level):
    from stats import derive_item_pct, UPGRADE_STEP
    try:
        from cogs.shop import get_affinity_multiplier
        aff = get_affinity_multiplier(item.get('name', ''), race)
    except Exception:
        aff = 1.0
    up = 1 + UPGRADE_STEP * (level - 1)
    return {k: v * aff * up for k, v in derive_item_pct(item).items()}


class ForgeView(discord.ui.View):
    def __init__(self, ctx, uid):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.uid = uid
        self.message = None

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your forge!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="YES", emoji="✅", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(self.ctx.author.id)
        found = players.search(Player.id == user_id)
        if not found:
            await interaction.response.send_message("Player not found.", ephemeral=True)
            return
        p = found[0]
        inv = p.get('inventory', [])
        item = next((i for i in inv if str(i.get('uid')) == self.uid), None)
        if not item:
            await interaction.response.edit_message(
                embed=discord.Embed(description="❌ That item is no longer in your inventory.", color=GOLD), view=None)
            self.stop()
            return

        level = item.get('upgrade_level', 1)
        if level >= MAX_UPGRADE_LEVEL:
            await interaction.response.edit_message(
                embed=discord.Embed(description="⭐ This item is already at max level!", color=GOLD), view=None)
            self.stop()
            return

        cost = forge_cost(item)
        have = p.get('nexite', 0)
        if have < cost:
            await interaction.response.edit_message(
                embed=discord.Embed(description=f"❌ Not enough Nexite! Need `{cost}`, you have `{have}`.", color=GOLD),
                view=None)
            self.stop()
            return

        race = p.get('race')
        new_level = level + 1
        item['upgrade_level'] = new_level
        equipped = p.get('equipped') or {}
        for slot, eq in equipped.items():
            if eq and isinstance(eq, dict) and str(eq.get('uid')) == self.uid:
                eq['upgrade_level'] = new_level

        players.update({'nexite': have - cost, 'inventory': inv, 'equipped': equipped}, Player.id == user_id)

        new_pct = pct_at_level(item, race, new_level)
        lines = "\n".join(f"• {stat_label(k)} Bonus: +{v:.1f}%" for k, v in new_pct.items())
        embed = discord.Embed(title="✅ NEXITE UPGRADE", color=GOLD)
        embed.description = f"Your **{item.get('name', 'item')}** has been successfully upgraded!"
        embed.add_field(name="⭐ Upgrade Level", value=f"{level} → {new_level}", inline=False)
        embed.add_field(name="📊 Updated Stats", value=lines or "—", inline=False)
        embed.add_field(name=f"{NEXITE_ICON} Nexite Used", value=f"`{cost}`  (left: `{have - cost}`)", inline=False)
        embed.set_footer(text="✨ Your equipment has become stronger!")
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()

    @discord.ui.button(label="NO", emoji="❌", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(description="Upgrade cancelled.", color=GOLD), view=None)
        self.stop()

    async def on_timeout(self):
        if self.message:
            try:
                await self.message.edit(
                    embed=discord.Embed(description="⏰ Forge timed out.", color=GOLD), view=None)
            except Exception:
                pass


class Forge(commands.Cog, name="Forge"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="forge", aliases=["upgrade", "nf"])
    async def forge(self, ctx, item_id: str = None):
        if not item_id:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!forge <item id>`\nUse the number from `!inv`. Works on weapons, armor and head armor.",
                color=GOLD))
            return

        user_id = str(ctx.author.id)
        found = players.search(Player.id == user_id)
        if not found:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
            return
        p = found[0]

        uid = str(item_id).strip().strip('()')
        item = next((i for i in p.get('inventory', []) if str(i.get('uid')) == uid), None)
        if not item:
            await ctx.send(embed=discord.Embed(description=f"❌ Item `{uid}` not found in your inventory!", color=GOLD))
            return

        if item.get('type') not in FORGEABLE_TYPES:
            await ctx.send(embed=discord.Embed(
                description="❌ Only weapons, armor and head armor can be upgraded.", color=GOLD))
            return

        race = p.get('race')
        level = item.get('upgrade_level', 1)
        cur = pct_at_level(item, race, level)
        if not cur:
            await ctx.send(embed=discord.Embed(description="❌ This item has no stats to upgrade.", color=GOLD))
            return

        if level >= MAX_UPGRADE_LEVEL:
            await ctx.send(embed=discord.Embed(
                description=f"⭐ **{item.get('name')}** is already at max level ({MAX_UPGRADE_LEVEL})!", color=GOLD))
            return

        nxt = pct_at_level(item, race, level + 1)
        cost = forge_cost(item)
        have = p.get('nexite', 0)

        cur_lines = "\n".join(f"• {stat_label(k)} Bonus: +{v:.1f}%" for k, v in cur.items())
        prev_lines = "\n".join(
            f"• {stat_label(k)} Bonus: +{cur[k]:.1f}% → +{nxt[k]:.1f}%" for k in cur)

        rarity = item.get('rarity', 'Common')
        embed = discord.Embed(title="⚒️ NEXFORGE", color=GOLD)
        embed.add_field(name="🗡️ Equipment", value=f"**{item.get('name')}**  `({uid})`", inline=False)
        embed.add_field(name="⭐ Rarity", value=f"{RARITY_ICONS.get(rarity, '⚪')} {rarity}", inline=False)
        embed.add_field(name="📊 Current Stats", value=f"{cur_lines}\n• Upgrade Level: {level}", inline=False)
        embed.add_field(name="✨ Upgrade Preview", value=f"{prev_lines}\n• Level: {level} → {level + 1}", inline=False)
        embed.add_field(name="💎 Materials Required", value=f"• {NEXITE_ICON} Nexite: **{cost}**", inline=False)
        embed.add_field(name=f"{NEXITE_ICON} Your Nexite", value=f"`{have}`", inline=False)

        if have < cost:
            embed.set_footer(text=f"❌ You need {cost - have} more Nexite to upgrade this.")
            await ctx.send(embed=embed)
            return

        embed.set_footer(text="Are you sure you want to upgrade?")
        view = ForgeView(ctx, uid)
        view.message = await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Forge(bot))
