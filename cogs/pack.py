import discord
from discord.ext import commands
from db import players, Player, generate_item_uid
import random
import time

GOLD = 0xFFD700
ITEMPACK_EMOJI = "<:itempack:1533458814613852261>"
PETPACK_EMOJI = "<:petpack:1533458731612897441>"

ITEM_PACK_PRICE = 10000

ITEM_PACK_POOL = {
    'Rare': [
        {"name": "Steel Broadsword",        "type": "weapon", "stats": {"str": 20}},
        {"name": "Iron Battleaxe",           "type": "weapon", "stats": {"str": 28}},
        {"name": "Assassin's Dagger",        "type": "weapon", "stats": {"str": 14}},
        {"name": "Heavy Warhammer",          "type": "weapon", "stats": {"str": 32}},
        {"name": "Heavy Iron Plate",         "type": "armor",  "stats": {"def": 30}},
        {"name": "Hardened Leather Jerkin",  "type": "armor",  "stats": {"def": 18}},
        {"name": "Chainmail Hauberk",        "type": "armor",  "stats": {"def": 25, "hp": 50}},
    ],
    'Epic': [
        {"name": "Demonic Longsword",        "type": "weapon", "stats": {"str": 55}},
        {"name": "Crystal Staff",            "type": "weapon", "stats": {"mag": 45}},
        {"name": "Greatsword of Flame",      "type": "weapon", "stats": {"str": 65}},
        {"name": "Knight-Captain's Plate",   "type": "armor",  "stats": {"def": 75, "hp": 60}},
        {"name": "Obsidian Carapace",        "type": "armor",  "stats": {"def": 90}},
    ],
    'Legendary': [
        {"name": "Excalibur",                "type": "weapon", "stats": {"str": 150, "hp": 50}},
        {"name": "Void-Rift Blade",          "type": "weapon", "stats": {"str": 140}},
        {"name": "Dragonscale Breastplate",  "type": "armor",  "stats": {"def": 200, "hp": 150}},
        {"name": "Immortal's Bulwark",       "type": "armor",  "stats": {"def": 350, "hp": 200}},
    ],
}
ITEM_PACK_RARITIES_NORMAL = ['Rare', 'Rare', 'Rare', 'Rare', 'Epic', 'Epic', 'Epic', 'Legendary', 'Legendary']
ITEM_PACK_RARITIES_LUCKY  = ['Rare', 'Rare', 'Epic', 'Epic', 'Epic', 'Legendary', 'Legendary', 'Legendary']

PET_PACK_PRICE = 100
PACK_COOLDOWN_SECONDS = 3600
PET_PACK_RARITIES_NORMAL = ['Common', 'Common', 'Common', 'Common',
                             'Uncommon', 'Uncommon', 'Uncommon',
                             'Rare', 'Rare',
                             'Epic',
                             'Legendary']
PET_PACK_RARITIES_LUCKY  = ['Common', 'Common',
                             'Uncommon', 'Uncommon', 'Uncommon',
                             'Rare', 'Rare', 'Rare',
                             'Epic', 'Epic',
                             'Legendary', 'Legendary',
                             'Mythic']

RARITY_ICONS = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵",
                "Epic": "🟣", "Legendary": "🟠", "Mythic": "🔴", "Divine": "🟡"}

class PackView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    async def _check_user(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your pack menu!", ephemeral=True)
            return False
        return True

    async def _check_pack_cooldown(self, interaction, player, field, label):
        remaining = PACK_COOLDOWN_SECONDS - (time.time() - player.get(field, 0))
        if remaining <= 0:
            return True
        minutes, seconds = divmod(int(remaining), 60)
        hours, minutes = divmod(minutes, 60)
        if hours:
            available = f"{hours}h {minutes}m"
        else:
            available = f"{minutes}m {seconds}s"
        await interaction.response.send_message(
            f"⏰ {label} on cooldown! Available in **{available}**.",
            ephemeral=True)
        return False

    @discord.ui.button(label=f"Buy Item Pack — {ITEM_PACK_PRICE:,} NC", style=discord.ButtonStyle.blurple, emoji=ITEMPACK_EMOJI)
    async def buy_item_pack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user(interaction):
            return
        user_id = str(self.ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await interaction.response.send_message("You haven't started yet!", ephemeral=True)
            return
        p = p[0]
        if not await self._check_pack_cooldown(
                interaction, p, 'last_item_pack', 'Item Pack'):
            return
        if p.get('nexcoins', 0) < ITEM_PACK_PRICE:
            await interaction.response.send_message(
                f"❌ Not enough Nexcoins! Cost: {ITEM_PACK_PRICE:,} • Your balance: {p.get('nexcoins', 0):,}",
                ephemeral=True)
            return

        luck_active = time.time() < p.get('buff_luck_until', 0)
        pool = ITEM_PACK_RARITIES_LUCKY if luck_active else ITEM_PACK_RARITIES_NORMAL
        rolled_rarity = random.choice(pool)
        item_pool = ITEM_PACK_POOL.get(rolled_rarity, ITEM_PACK_POOL['Rare'])
        item_result = random.choice(item_pool)

        inv = p.get('inventory', [])
        uid = generate_item_uid()
        stats = item_result.get('stats', {})
        stat_desc = ", ".join([f"+{v} {k.upper()}" for k, v in stats.items()])
        inv.append({'uid': uid, 'name': item_result['name'], 'rarity': rolled_rarity,
                    'type': item_result['type'], 'description': stat_desc, 'stats': stats})
        new_coins = p.get('nexcoins', 0) - ITEM_PACK_PRICE
        players.update({
            'nexcoins': new_coins,
            'inventory': inv,
            'last_item_pack': time.time()
        }, Player.id == user_id)

        icon = RARITY_ICONS.get(rolled_rarity, '📦')
        embed = discord.Embed(title=f"{ITEMPACK_EMOJI} Item Pack Opened!", color=GOLD)
        embed.add_field(name="You got!", value=f"{icon} **{item_result['name']}** `{rolled_rarity}` (ID: `{uid}`)", inline=False)
        embed.add_field(name="Stats", value=stat_desc or "—", inline=True)
        embed.add_field(name="Remaining Nexcoins", value=f"`{new_coins:,}`", inline=True)
        if luck_active:
            embed.set_footer(text="🍀 Luck Potion active — boosted rarity chances!")
        else:
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label=f"Buy Pet Pack — {PET_PACK_PRICE} SS", style=discord.ButtonStyle.green, emoji=PETPACK_EMOJI)
    async def buy_pet_pack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user(interaction):
            return
        user_id = str(self.ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await interaction.response.send_message("You haven't started yet!", ephemeral=True)
            return
        p = p[0]
        if not await self._check_pack_cooldown(
                interaction, p, 'last_pet_pack', 'Pet Pack'):
            return
        if p.get('starshards', 0) < PET_PACK_PRICE:
            await interaction.response.send_message(
                f"❌ Not enough Starshards! Cost: {PET_PACK_PRICE} • Your balance: {p.get('starshards', 0)}",
                ephemeral=True)
            return

        from cogs.shop import PETS
        luck_active = time.time() < p.get('buff_luck_until', 0)
        pool = PET_PACK_RARITIES_LUCKY if luck_active else PET_PACK_RARITIES_NORMAL
        rolled_rarity = random.choice(pool)
        pet_pool = [pet for pet in PETS if pet['rarity'] == rolled_rarity]
        if not pet_pool:
            pet_pool = [pet for pet in PETS if pet['rarity'] == 'Common']
        pet = random.choice(pet_pool)

        inv = p.get('inventory', [])
        uid = generate_item_uid()
        inv.append({'uid': uid, 'name': pet['name'], 'rarity': pet['rarity'], 'type': 'pet',
                    'description': pet.get('description', ''), 'stats': pet.get('stats', {}),
                    'passive': pet.get('passive'), 'passive_desc': pet.get('passive_desc')})
        new_ss = p.get('starshards', 0) - PET_PACK_PRICE
        players.update({
            'starshards': new_ss,
            'inventory': inv,
            'last_pet_pack': time.time()
        }, Player.id == user_id)

        icon = RARITY_ICONS.get(pet['rarity'], '✨')
        embed = discord.Embed(title=f"{PETPACK_EMOJI} Pet Pack Opened!", color=GOLD)
        embed.add_field(name="You got!", value=f"{icon} **{pet['name']}** `{pet['rarity']}` (ID: `{uid}`)", inline=False)
        embed.add_field(name="Stats", value=pet.get('description', ''), inline=True)
        embed.add_field(name="Remaining Starshards", value=f"`{new_ss}`", inline=True)
        if luck_active:
            embed.set_footer(text="🍀 Luck Potion active — boosted rarity chances!")
        else:
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await interaction.response.send_message(embed=embed)

class Pack(commands.Cog, name="Pack"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pack")
    async def pack(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`", color=GOLD))
            return

        embed = discord.Embed(title="🎁 Nexworld Packs", color=GOLD)
        embed.add_field(
            name=f"{ITEMPACK_EMOJI} Item Pack",
            value=f"Open for a random weapon or armor! Rare → Legendary.\nPrice: `{ITEM_PACK_PRICE:,}` Nexcoins",
            inline=False)
        embed.add_field(
            name=f"{PETPACK_EMOJI} Pet Pack",
            value=f"Open for a random pet! Common → Mythic chances.\nPrice: `{PET_PACK_PRICE}` Starshards",
            inline=False)
        embed.set_footer(text="🍀 Luck Potions boost your rarity chances! • Nexworld RPG")
        await ctx.send(embed=embed, view=PackView(ctx))

async def setup(bot):
    await bot.add_cog(Pack(bot))
