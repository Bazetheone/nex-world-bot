import discord
from discord.ext import commands
from db import players, Player
from stats import get_effective_stats, magic_bar, derive_item_pct

GOLD = 0xFFD700


class StatCheck(commands.Cog, name="StatCheck"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="statcheck")
    async def statcheck(self, ctx, member: discord.Member = None):
        try:
            from main import ADMIN_IDS
            allowed = str(ctx.author.id) in [str(a) for a in ADMIN_IDS]
        except Exception:
            allowed = False
        if not allowed:
            await ctx.send("❌ Admins only.")
            return

        member = member or ctx.author
        found = players.search(Player.id == str(member.id))
        if not found:
            await ctx.send("❌ Player not found.")
            return
        p = found[0]
        eff, base, bonus = get_effective_stats(p)

        embed = discord.Embed(title=f"📊 Stat Preview: {member.display_name} ({p.get('race')})", color=GOLD)
        embed.add_field(
            name="Saved now",
            value=f"HP `{p.get('hp', 0):,}` • STR `{p.get('str', 0):,}` • DEF `{p.get('def', 0):,}` • MAG `{p.get('mag', 0):,}`",
            inline=False)
        embed.add_field(
            name="Base without old flat gear",
            value=f"HP `{base['hp']:,}` • STR `{base['str']:,}` • DEF `{base['def']:,}` • MAG `{base['mag']:,}`",
            inline=False)
        embed.add_field(
            name="Gear and pet bonus (new)",
            value=f"HP +{bonus['hp']:.1f}% • STR +{bonus['str']:.1f}% • DEF +{bonus['def']:.1f}% • Magic Power +{bonus['mag']:.1f}",
            inline=False)
        embed.add_field(
            name="Effective stats (new)",
            value=f"HP `{eff['hp']:,}` • STR `{eff['str']:,}` • DEF `{eff['def']:,}`",
            inline=False)
        embed.add_field(name="Magic Power", value=magic_bar(eff['magic_power_pct']), inline=False)

        lines = []
        for slot, item in (p.get('equipped') or {}).items():
            if item and isinstance(item, dict):
                pct = derive_item_pct(item, is_pet=(slot == 'pet'))
                parts = ", ".join(f"+{v:g}% {k.upper()}" for k, v in pct.items()) or "no stats"
                lines.append(f"**{item.get('name', '?')}** ({slot}): {parts}")
        embed.add_field(name="Equipped items (new %)", value="\n".join(lines) or "Nothing equipped", inline=False)
        embed.set_footer(text=f"Preview only, nothing changed • stats_version {p.get('stats_version', 1)}")
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(StatCheck(bot))
