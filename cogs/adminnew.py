import discord
import shutil
import time
from discord.ext import commands
from db import players, Player

GOLD = 0xFFD700
NEXITE_ICON = "<:nexite:1567658459342831636>"


def is_admin(ctx):
    try:
        from main import ADMIN_IDS
        return str(ctx.author.id) in [str(a) for a in ADMIN_IDS]
    except Exception:
        return False


def convert_player(p):
    eq = dict(p.get('equipped') or {})
    hp, st, mg, df = p.get('hp', 1), p.get('str', 1), p.get('mag', 1), p.get('def', 1)
    changed = 0
    for slot, item in list(eq.items()):
        if item and isinstance(item, dict) and not item.get('pct_mode'):
            for stat, val in (item.get('stats') or {}).items():
                if stat == 'hp':
                    hp = max(1, hp - val)
                elif stat == 'str':
                    st = max(1, st - val)
                elif stat == 'mag':
                    mg = max(1, mg - val)
                elif stat == 'def':
                    df = max(1, df - val)
            new_item = dict(item)
            new_item['pct_mode'] = True
            new_item.setdefault('upgrade_level', 1)
            eq[slot] = new_item
            changed += 1
    if changed:
        players.update({'equipped': eq, 'hp': hp, 'str': st, 'mag': mg, 'def': df},
                       Player.id == p['id'])
    return changed


class AdminNew(commands.Cog, name="AdminNew"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="givenexite")
    async def givenexite(self, ctx, member: discord.Member = None, amount: int = None):
        if not is_admin(ctx):
            await ctx.send("❌ Admins only.")
            return
        if member is None or amount is None or amount <= 0:
            await ctx.send("Usage: `!givenexite @user <amount>`")
            return
        found = players.search(Player.id == str(member.id))
        if not found:
            await ctx.send("❌ Player not found.")
            return
        new_val = found[0].get('nexite', 0) + amount
        players.update({'nexite': new_val}, Player.id == str(member.id))
        await ctx.send(embed=discord.Embed(
            description=f"{NEXITE_ICON} Gave **{amount:,}** Nexite to {member.mention}. They now have `{new_val:,}`.",
            color=GOLD))

    @commands.command(name="takenexite")
    async def takenexite(self, ctx, member: discord.Member = None, amount: int = None):
        if not is_admin(ctx):
            await ctx.send("❌ Admins only.")
            return
        if member is None or amount is None or amount <= 0:
            await ctx.send("Usage: `!takenexite @user <amount>`")
            return
        found = players.search(Player.id == str(member.id))
        if not found:
            await ctx.send("❌ Player not found.")
            return
        new_val = max(0, found[0].get('nexite', 0) - amount)
        players.update({'nexite': new_val}, Player.id == str(member.id))
        await ctx.send(embed=discord.Embed(
            description=f"{NEXITE_ICON} Took **{amount:,}** Nexite from {member.mention}. They now have `{new_val:,}`.",
            color=GOLD))

    @commands.command(name="convertgear")
    async def convertgear(self, ctx, target: str = None):
        if not is_admin(ctx):
            await ctx.send("❌ Admins only.")
            return
        if not target:
            await ctx.send("Usage: `!convertgear @user` or `!convertgear all`")
            return

        if target.lower() == 'all':
            try:
                shutil.copy('nexworld.json', f'nexworld_backup_{int(time.time())}.json')
            except Exception as e:
                await ctx.send(f"❌ Backup failed ({e}). Nothing was changed.")
                return
            items = 0
            people = 0
            for p in players.all():
                c = convert_player(p)
                if c:
                    items += c
                    people += 1
            await ctx.send(embed=discord.Embed(
                description=f"✅ Backup saved. Converted **{items}** equipped item(s) across **{people}** player(s) to percentage mode.",
                color=GOLD))
            return

        uid = target.strip('<@!>')
        found = players.search(Player.id == uid)
        if not found:
            await ctx.send("❌ Player not found.")
            return
        c = convert_player(found[0])
        await ctx.send(embed=discord.Embed(
            description=f"✅ Converted **{c}** equipped item(s) to percentage mode. Their final stats did not change.",
            color=GOLD))


async def setup(bot):
    await bot.add_cog(AdminNew(bot))
