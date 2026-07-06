import discord
from discord.ext import commands
from db import players, Player
import random
import time

GOLD = 0xFFD700

NEXCOIN_SHOP = [
    {"id": 1,  "name": "Small HP Potion",          "description": "Restores 15% of max HP in battle",                                               "price": 500,    "rarity": "Common",    "type": "consumable", "stats": {}},
    {"id": 2,  "name": "Item Pack",               "description": "Open for a random weapon or armor! Rare → Legendary. Luck Potion boosts chances!", "price": 1000,   "rarity": "Special",   "type": "itempack",   "stats": {}},
    {"id": 3,  "name": "Medium HP Potion",        "description": "Restores 30% of max HP in battle",                                               "price": 1500,   "rarity": "Uncommon",  "type": "consumable", "stats": {}},
    {"id": 4,  "name": "EXP Boost Potion",        "description": "Doubles EXP gained for 5 minutes. Use with `!usebuff <uid>`",                    "price": 2000,   "rarity": "Uncommon",  "type": "buff",       "stats": {}},
    {"id": 5,  "name": "Luck Potion",             "description": "Boosts drop luck & pet pack rarity for 5 minutes. Use with `!usebuff <uid>`",    "price": 3000,   "rarity": "Rare",      "type": "buff",       "stats": {}},
    {"id": 6,  "name": "Large HP Potion",         "description": "Restores 50% of max HP in battle",                                               "price": 5000,   "rarity": "Rare",      "type": "consumable", "stats": {}},
    {"id": 7,  "name": "Steel Broadsword",        "description": "+20 Attack",                                                                      "price": 5000,   "rarity": "Rare",      "type": "weapon",     "stats": {"str": 20}},
    {"id": 8,  "name": "Iron Battleaxe",          "description": "+28 Attack",                                                                      "price": 5000,   "rarity": "Rare",      "type": "weapon",     "stats": {"str": 28}},
    {"id": 9,  "name": "Assassin's Dagger",       "description": "+14 Attack",                                                                      "price": 5000,   "rarity": "Rare",      "type": "weapon",     "stats": {"str": 14}},
    {"id": 10, "name": "Heavy Warhammer",         "description": "+32 Attack",                                                                      "price": 5000,   "rarity": "Rare",      "type": "weapon",     "stats": {"str": 32}},
    {"id": 11, "name": "Heavy Iron Plate",        "description": "+30 Defense",                                                                     "price": 10000,  "rarity": "Rare",      "type": "armor",      "stats": {"def": 30}},
    {"id": 12, "name": "Hardened Leather Jerkin", "description": "+18 Defense",                                                                     "price": 10000,  "rarity": "Rare",      "type": "armor",      "stats": {"def": 18}},
    {"id": 13, "name": "Chainmail Hauberk",       "description": "+25 Defense, +50 Health",                                                         "price": 10000,  "rarity": "Rare",      "type": "armor",      "stats": {"def": 25, "hp": 50}},
    {"id": 14, "name": "DEF Boost Potion",        "description": "+100 DEF for 5 minutes. Use with `!usebuff <uid>`",                              "price": 10000,  "rarity": "Rare",      "type": "buff",       "stats": {"def": 100}},
    {"id": 15, "name": "Demonic Longsword",       "description": "+55 Attack",                                                                      "price": 15000,  "rarity": "Epic",      "type": "weapon",     "stats": {"str": 55}},
    {"id": 16, "name": "Crystal Staff",           "description": "+45 Magic Attack",                                                                "price": 15000,  "rarity": "Epic",      "type": "weapon",     "stats": {"mag": 45}},
    {"id": 17, "name": "Greatsword of Flame",     "description": "+65 Attack",                                                                      "price": 15000,  "rarity": "Epic",      "type": "weapon",     "stats": {"str": 65}},
    {"id": 18, "name": "Raid Pass",               "description": "Used to summon a raid boss",                                                      "price": 15000,  "rarity": "Rare",      "type": "consumable", "stats": {}},
    {"id": 19, "name": "STR Boost Potion",        "description": "+100 STR & +100 MAG for 5 minutes. Use with `!usebuff <uid>`",                   "price": 15000,  "rarity": "Epic",      "type": "buff",       "stats": {"str": 100, "mag": 100}},
    {"id": 20, "name": "Knight-Captain's Plate",  "description": "+75 Defense, +60 Health",                                                         "price": 30000,  "rarity": "Epic",      "type": "armor",      "stats": {"def": 75, "hp": 60}},
    {"id": 21, "name": "Obsidian Carapace",       "description": "+90 Defense",                                                                     "price": 30000,  "rarity": "Epic",      "type": "armor",      "stats": {"def": 90}},
    {"id": 22, "name": "Excalibur",               "description": "+150 Attack, +50 Health",                                                         "price": 50000,  "rarity": "Legendary", "type": "weapon",     "stats": {"str": 150, "hp": 50}},
    {"id": 23, "name": "Void-Rift Blade",         "description": "+140 Attack",                                                                     "price": 50000,  "rarity": "Legendary", "type": "weapon",     "stats": {"str": 140}},
    {"id": 24, "name": "Dragonscale Breastplate", "description": "+200 Defense, +150 Health",                                                       "price": 100000, "rarity": "Legendary", "type": "armor",      "stats": {"def": 200, "hp": 150}},
    {"id": 25, "name": "Immortal's Bulwark",      "description": "+350 Defense, +200 Health",                                                       "price": 100000, "rarity": "Legendary", "type": "armor",      "stats": {"def": 350, "hp": 200}},
]

SS_SHOP = [
    {"id": 1,  "name": "Race Reroll Token",         "description": "Reroll your race with higher chances of Rare/Primordial", "price": 500, "rarity": "Legendary", "type": "consumable", "stats": {}},
    {"id": 2,  "name": "World-Breaker Greatsword",  "description": "+500 Attack",                           "price": 150, "rarity": "Mythic", "type": "weapon",  "stats": {"str": 500}},
    {"id": 3,  "name": "Staff of Infinite Cosmos",  "description": "+450 Magic Attack",                     "price": 150, "rarity": "Mythic", "type": "weapon",  "stats": {"mag": 450}},
    {"id": 4,  "name": "Abyss-Forged Plating",      "description": "+800 Defense, +400 Health",             "price": 200, "rarity": "Mythic", "type": "armor",   "stats": {"def": 800, "hp": 400}},
    {"id": 5,  "name": "Robes of Cosmic Balance",   "description": "+60 Magic Attack",                      "price": 200, "rarity": "Mythic", "type": "armor",   "stats": {"mag": 60}},
    {"id": 6,  "name": "Halo of the Seraphim",      "description": "+500 Health, +300 Defense",             "price": 300, "rarity": "Godly",  "type": "head_armor", "stats": {"hp": 500, "def": 300}},
    {"id": 7,  "name": "Crown of Eternal Void",     "description": "+80 Magic Attack",                      "price": 300, "rarity": "Godly",  "type": "head_armor", "stats": {"mag": 80}},
    {"id": 8,  "name": "Ragnarok Executioner",      "description": "+600 Attack",                            "price": 350, "rarity": "Godly",  "type": "weapon",  "stats": {"str": 600}},
    {"id": 9,  "name": "Apocalypse Scythe",         "description": "+550 Attack",                            "price": 350, "rarity": "Godly",  "type": "weapon",  "stats": {"str": 550}},
    {"id": 10, "name": "Pet Pack",                  "description": "Open for a random pet! Common → Mythic chances. Luck Potion boosts rarity!", "price": 100, "rarity": "Special", "type": "petpack", "stats": {}},
]

PETS = [
    {"id": 1,  "name": "Baby Direwolf",       "description": "+18 Attack",                              "price": 10,  "rarity": "Common",    "stats": {"str": 18}},
    {"id": 2,  "name": "Ember Fox",           "description": "+15 Magic Attack",                        "price": 10,  "rarity": "Common",    "stats": {"mag": 15}},
    {"id": 3,  "name": "Stone Turtle",        "description": "+22 Defense",                             "price": 10,  "rarity": "Common",    "stats": {"def": 22}},
    {"id": 4,  "name": "Pixie",               "description": "+25 Magic Attack",                        "price": 15,  "rarity": "Uncommon",  "stats": {"mag": 25}},
    {"id": 5,  "name": "Barn Owl",            "description": "+15 Attack, +10 Defense",                 "price": 15,  "rarity": "Uncommon",  "stats": {"str": 15, "def": 10}},
    {"id": 6,  "name": "Razorbeak Falcon",    "description": "+18 Attack",                              "price": 15,  "rarity": "Uncommon",  "stats": {"str": 18}},
    {"id": 7,  "name": "Shadow Panther",      "description": "+35 Attack",                              "price": 30,  "rarity": "Rare",      "stats": {"str": 35}},
    {"id": 8,  "name": "Storm Eagle",         "description": "+25 Attack, +15 Magic Attack",            "price": 30,  "rarity": "Rare",      "stats": {"str": 25, "mag": 15}},
    {"id": 9,  "name": "Pyre Drake",          "description": "+35 Attack, +15 Magic Attack",            "price": 30,  "rarity": "Rare",      "stats": {"str": 35, "mag": 15}},
    {"id": 10, "name": "Ironbark Treant",     "description": "+70 Defense",                             "price": 40,  "rarity": "Epic",      "stats": {"def": 70}},
    {"id": 11, "name": "Treasure Goblin",     "description": "+100 Health, +25 Attack",                 "price": 40,  "rarity": "Epic",      "stats": {"hp": 100, "str": 25}},
    {"id": 12, "name": "Void Tadpole",        "description": "+60 Magic Attack, +50 Health",            "price": 40,  "rarity": "Epic",      "stats": {"mag": 60, "hp": 50}},
    {"id": 13, "name": "Griffin Hatchling",   "description": "+90 Attack, +40 Defense",                 "price": 60,  "rarity": "Legendary", "stats": {"str": 90, "def": 40}},
    {"id": 14, "name": "Phoenix Chick",       "description": "+400 Health, +50 Magic Attack",           "price": 60,  "rarity": "Legendary", "stats": {"hp": 400, "mag": 50}},
    {"id": 15, "name": "Vampiric Bat",        "description": "+80 Attack, +120 Health",                 "price": 60,  "rarity": "Legendary", "stats": {"str": 80, "hp": 120}},
    {"id": 16, "name": "Astral Dragon",       "description": "+220 Attack, +180 Magic Attack, +100 HP", "price": 100, "rarity": "Mythic",    "stats": {"str": 220, "mag": 180, "hp": 100}},
    {"id": 17, "name": "Void Leviathan",      "description": "+650 Health, +120 Defense",               "price": 100, "rarity": "Mythic",    "stats": {"hp": 650, "def": 120}},
    {"id": 18, "name": "Golden Kirin",        "description": "+100 Attack, +100 Magic Attack, +100 DEF","price": 100, "rarity": "Mythic",    "stats": {"str": 100, "mag": 100, "def": 100}},
    {"id": 19, "name": "Cybernetic Behemoth", "description": "+380 Defense, +200 Health",               "price": 100, "rarity": "Mythic",    "stats": {"def": 380, "hp": 200}},
    {"id": 20, "name": "Seraphic Pegasus",    "description": "+750 Health, +120 Magic Attack",          "price": 100, "rarity": "Divine",    "stats": {"hp": 750, "mag": 120}},
    {"id": 21, "name": "Chaos Hydra",         "description": "+350 Attack, +120 Magic Attack",          "price": 100, "rarity": "Divine",    "stats": {"str": 350, "mag": 120}},
    {"id": 22, "name": "Time-Keeper Sphinx",  "description": "+250 HP, +180 ATK, +180 MAG, +120 DEF",  "price": 100, "rarity": "Divine",    "stats": {"hp": 250, "str": 180, "mag": 180, "def": 120}},
]

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

PET_PACK_RARITIES_NORMAL = ['Common', 'Common', 'Common', 'Common',
                             'Uncommon', 'Uncommon', 'Uncommon',
                             'Rare', 'Rare',
                             'Epic',
                             'Legendary',]
PET_PACK_RARITIES_LUCKY  = ['Common', 'Common',
                             'Uncommon', 'Uncommon', 'Uncommon',
                             'Rare', 'Rare', 'Rare',
                             'Epic', 'Epic',
                             'Legendary', 'Legendary',
                             'Mythic',]

def get_daily_shop():
    random.seed(int(time.time() // 86400))
    daily_items = random.sample(NEXCOIN_SHOP[:16], 4)
    daily_pet = random.choice(PETS)
    random.seed()
    return daily_items, daily_pet

def time_until_reset():
    now = time.time()
    next_reset = (int(now // 86400) + 1) * 86400
    remaining = next_reset - now
    hours = int(remaining // 3600)
    minutes = int((remaining % 3600) // 60)
    return f"{hours}h {minutes}m"

_NEXCOIN_ITEMS_PER_PAGE = 11

def build_nexcoin_shop_embed(page=1):
    sorted_items = sorted(NEXCOIN_SHOP, key=lambda x: x['price'])
    total_pages = max(1, (len(sorted_items) + _NEXCOIN_ITEMS_PER_PAGE - 1) // _NEXCOIN_ITEMS_PER_PAGE)
    page = max(1, min(page, total_pages))
    start = (page - 1) * _NEXCOIN_ITEMS_PER_PAGE
    page_items = sorted_items[start:start + _NEXCOIN_ITEMS_PER_PAGE]
    embed = discord.Embed(title=f"💰 Nexcoin Shop  (Page {page}/{total_pages})", color=GOLD)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    for item in page_items:
        embed.add_field(
            name=f"({item['id']}) {item['name']} — `{item['rarity']}`",
            value=f"Price: `{item['price']:,}` Nexcoins\n{item['description']}",
            inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    embed.add_field(name="How to Buy", value="`!buy 1 <item id>`", inline=False)
    embed.set_footer(text="Nexworld RPG • Use ◀ ▶ to browse pages")
    return embed

def build_ss_shop_embed():
    sorted_items = sorted(SS_SHOP, key=lambda x: x['price'])
    embed = discord.Embed(title="✨ Starshard Shop", color=GOLD)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    for item in sorted_items:
        embed.add_field(
            name=f"({item['id']}) {item['name']} — `{item['rarity']}`",
            value=f"Price: `{item['price']}` Starshards\n{item['description']}",
            inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    embed.add_field(name="How to Buy", value="`!buy 2 <item id>`", inline=False)
    embed.set_footer(text="Nexworld RPG • Your fate has been decided")
    return embed

def build_daily_shop_embed():
    daily_items, daily_pet = get_daily_shop()
    embed = discord.Embed(
        title="🔄 Daily Shop",
        description=f"Resets in: **{time_until_reset()}**",
        color=GOLD)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    for i, item in enumerate(daily_items, 1):
        embed.add_field(
            name=f"({i}) {item['name']} — `{item['rarity']}`",
            value=f"Price: `{item['price']:,}` Nexcoins\n{item['description']}",
            inline=False)
    embed.add_field(
        name=f"(5) {daily_pet['name']} — `{daily_pet['rarity']}` Pet",
        value=f"Price: `{daily_pet['price']}` Starshards\n{daily_pet['description']}",
        inline=False)
    embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
    embed.add_field(name="How to Buy", value="`!buy daily <1-5>`", inline=False)
    embed.set_footer(text="Nexworld RPG • Your fate has been decided")
    return embed

class BuyConfirmView(discord.ui.View):
    def __init__(self, ctx, item_name, cost, cost_type):
        super().__init__(timeout=30)
        self.ctx = ctx
        self.confirmed = False
        self.embed_title = f"🛒 Confirm Purchase: **{item_name}**"
        self.cost_str = f"`{cost:,}` {'Nexcoins' if cost_type == 'nexcoins' else 'Starshards'}"

    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.green)
    async def confirm_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your purchase!", ephemeral=True)
            return
        self.confirmed = True
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.red)
    async def cancel_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your purchase!", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=discord.Embed(description="❌ Purchase cancelled.", color=GOLD), view=None)
        self.stop()


class NexcoinShopView(discord.ui.View):
    def __init__(self, ctx, page=1):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.page = page

    @discord.ui.button(label="◀ Prev", style=discord.ButtonStyle.grey)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        if self.page > 1:
            self.page -= 1
        await interaction.response.edit_message(embed=build_nexcoin_shop_embed(self.page), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.grey)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        total_pages = max(1, (len(NEXCOIN_SHOP) + _NEXCOIN_ITEMS_PER_PAGE - 1) // _NEXCOIN_ITEMS_PER_PAGE)
        if self.page < total_pages:
            self.page += 1
        await interaction.response.edit_message(embed=build_nexcoin_shop_embed(self.page), view=self)

    @discord.ui.button(label="🔙 Back to Menu", style=discord.ButtonStyle.blurple)
    async def back_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_daily_shop_embed(), view=ShopView(self.ctx))

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.red)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=discord.Embed(description="🛒 Shop closed.", color=GOLD), view=None)
        self.stop()

class ShopView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=60)
        self.ctx = ctx

    @discord.ui.button(label="💰 Nexcoin Shop", style=discord.ButtonStyle.blurple)
    async def nexcoin_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        await interaction.response.edit_message(embed=build_nexcoin_shop_embed(1), view=NexcoinShopView(self.ctx, 1))

    @discord.ui.button(label="✨ Starshard Shop", style=discord.ButtonStyle.green)
    async def ss_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        embed = build_ss_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="🔄 Daily Shop", style=discord.ButtonStyle.grey)
    async def daily_shop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        embed = build_daily_shop_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.red)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=discord.Embed(description="🛒 Shop closed.", color=GOLD), view=None)
        self.stop()

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx, shop_num: int = None):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(
                description="❌ You haven't started yet! Use `!start` to begin.",
                color=GOLD))
            return

        if shop_num == 1:
            await ctx.send(embed=build_nexcoin_shop_embed(1), view=NexcoinShopView(ctx, 1))
        elif shop_num == 2:
            await ctx.send(embed=build_ss_shop_embed(), view=ShopView(ctx))
        else:
            await ctx.send(embed=build_daily_shop_embed(), view=ShopView(ctx))

    @commands.command()
    async def buy(self, ctx, shop_num: str = None, item_num: int = None):
        if not shop_num or not item_num:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!buy <shop> <item>`\nExample: `!buy 1 5` or `!buy 2 1` or `!buy daily 3`",
                color=GOLD))
            return

        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            await ctx.send(embed=discord.Embed(
                description="❌ You haven't started yet!",
                color=GOLD))
            return

        p = p[0]

        if shop_num == "daily":
            daily_items, daily_pet = get_daily_shop()
            if item_num == 5:
                item = daily_pet
                cost_type = "starshards"
                cost = item['price']
                current = p.get('starshards', 0)
            elif 1 <= item_num <= 4:
                item = daily_items[item_num - 1]
                cost_type = "nexcoins"
                cost = item['price']
                current = p.get('nexcoins', 0)
            else:
                await ctx.send(embed=discord.Embed(description="❌ Invalid item number! Daily shop has items 1-5.", color=GOLD))
                return

        elif shop_num == "1":
            item = next((i for i in NEXCOIN_SHOP if i['id'] == item_num), None)
            if not item:
                await ctx.send(embed=discord.Embed(description="❌ Item not found!", color=GOLD))
                return
            cost_type = "nexcoins"
            cost = item['price']
            current = p.get('nexcoins', 0)

            if item.get('type') == 'itempack':
                if current < cost:
                    await ctx.send(embed=discord.Embed(
                        description=f"❌ Not enough Nexcoins!\nCost: `{cost:,}` • Your balance: `{current:,}`",
                        color=GOLD))
                    return
                luck_active = time.time() < p.get('buff_luck_until', 0)
                pool = ITEM_PACK_RARITIES_LUCKY if luck_active else ITEM_PACK_RARITIES_NORMAL
                rolled_rarity = random.choice(pool)
                item_pool = ITEM_PACK_POOL.get(rolled_rarity, ITEM_PACK_POOL['Rare'])
                item_result = random.choice(item_pool)
                fresh_p = players.search(Player.id == user_id)[0]
                inv = fresh_p.get('inventory', [])
                uid = str(random.randint(100000, 999999))
                stats = item_result.get('stats', {})
                stat_desc = ", ".join([f"+{v} {k.upper()}" for k, v in stats.items()])
                inv.append({'uid': uid, 'name': item_result['name'], 'rarity': rolled_rarity,
                            'type': item_result['type'], 'description': stat_desc, 'stats': stats})
                new_coins = fresh_p.get('nexcoins', 0) - cost
                players.update({'nexcoins': new_coins, 'inventory': inv}, Player.id == user_id)
                rarity_icons = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵",
                                "Epic": "🟣", "Legendary": "🟠", "Mythic": "🔴"}
                icon = rarity_icons.get(rolled_rarity, '📦')
                embed = discord.Embed(title="📦 Item Pack Opened!", color=GOLD)
                embed.add_field(name="You got!", value=f"{icon} **{item_result['name']}** `{rolled_rarity}`", inline=False)
                embed.add_field(name="Stats", value=stat_desc or "—", inline=True)
                embed.add_field(name="Remaining Nexcoins", value=f"`{new_coins:,}`", inline=True)
                if luck_active:
                    embed.set_footer(text="🍀 Luck Potion active — boosted rarity chances!")
                else:
                    embed.set_footer(text="Nexworld RPG • Your fate has been decided")
                await ctx.send(embed=embed)
                return

        elif shop_num == "2":
            item = next((i for i in SS_SHOP if i['id'] == item_num), None)
            if not item:
                await ctx.send(embed=discord.Embed(description="❌ Item not found!", color=GOLD))
                return
            cost_type = "starshards"
            cost = item['price']
            current = p.get('starshards', 0)

            if item.get('type') == 'petpack':
                if current < cost:
                    await ctx.send(embed=discord.Embed(
                        description=f"❌ Not enough Starshards!\nCost: `{cost}` • Your balance: `{current}`",
                        color=GOLD))
                    return
                luck_active = time.time() < p.get('buff_luck_until', 0)
                pool = PET_PACK_RARITIES_LUCKY if luck_active else PET_PACK_RARITIES_NORMAL
                rolled_rarity = random.choice(pool)
                pet_pool = [pet for pet in PETS if pet['rarity'] == rolled_rarity]
                if not pet_pool:
                    pet_pool = [pet for pet in PETS if pet['rarity'] == 'Common']
                pet = random.choice(pet_pool)
                fresh_p = players.search(Player.id == user_id)[0]
                inv = fresh_p.get('inventory', [])
                uid = str(random.randint(100000, 999999))
                inv.append({'uid': uid, 'name': pet['name'], 'rarity': pet['rarity'], 'type': 'pet',
                            'description': pet['description'], 'stats': pet.get('stats', {})})
                players.update({'starshards': current - cost, 'inventory': inv}, Player.id == user_id)
                rarity_icons = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵",
                                "Epic": "🟣", "Legendary": "🟠", "Mythic": "🔴", "Divine": "🟡"}
                icon = rarity_icons.get(pet['rarity'], '✨')
                embed = discord.Embed(title="🎁 Pet Pack Opened!", color=GOLD)
                embed.add_field(name="You got!", value=f"{icon} **{pet['name']}** `{pet['rarity']}`", inline=False)
                embed.add_field(name="Stats", value=pet['description'], inline=True)
                embed.add_field(name="Remaining Starshards", value=f"`{current - cost}`", inline=True)
                if luck_active:
                    embed.set_footer(text="🍀 Luck Potion active — boosted rarity chances!")
                else:
                    embed.set_footer(text="Nexworld RPG • Your fate has been decided")
                await ctx.send(embed=embed)
                return

        else:
            await ctx.send(embed=discord.Embed(
                description="❌ Invalid shop! Use `1`, `2`, or `daily`",
                color=GOLD))
            return

        if current < cost:
            currency = "Nexcoins" if cost_type == "nexcoins" else "Starshards"
            await ctx.send(embed=discord.Embed(
                description=f"❌ Not enough {currency}!\nCost: `{cost:,}` • Your balance: `{current:,}`",
                color=GOLD))
            return

        currency_name = "Nexcoins" if cost_type == "nexcoins" else "Starshards"
        confirm_view = BuyConfirmView(ctx, item['name'], cost, cost_type)
        confirm_embed = discord.Embed(
            title="🛒 Confirm Purchase",
            description=f"Buy **{item['name']}** for `{cost:,}` {currency_name}?",
            color=GOLD)
        confirm_msg = await ctx.send(embed=confirm_embed, view=confirm_view)
        await confirm_view.wait()
        if not confirm_view.confirmed:
            return

        if item['name'] == "Race Reroll Token":
            uid = str(random.randint(100000, 999999))
            new_item = {
                'uid': uid,
                'name': 'Race Reroll Token',
                'rarity': 'Legendary',
                'type': 'consumable'
            }
        else:
            uid = str(random.randint(100000, 999999))
            if shop_num == "daily" and item_num == 5:
                item_type = 'pet'
            else:
                item_type = item.get('type', 'item')
            new_item = {
                'uid': uid,
                'name': item['name'],
                'rarity': item['rarity'],
                'type': item_type,
                'description': item.get('description', ''),
                'stats': item.get('stats', {})
            }

        fresh_p = players.search(Player.id == user_id)
        if not fresh_p:
            await ctx.send(embed=discord.Embed(description="❌ Player data not found!", color=GOLD))
            return
        inv = fresh_p[0].get('inventory', [])
        inv.append(new_item)

        players.update({cost_type: current - cost, 'inventory': inv}, Player.id == user_id)

        embed = discord.Embed(
            title="✅ Purchase Successful!",
            description=f"You bought **{item['name']}**!",
            color=GOLD)
        embed.add_field(name="Cost", value=f"`{cost:,}` {currency_name}", inline=True)
        embed.add_field(name="New Balance", value=f"`{current - cost:,}` {currency_name}", inline=True)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command()
    async def usereroll(self, ctx):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
    await ctx.send(embed=discord.Embed(description="❌ You haven't started yet!", color=GOLD))
    return

        p = p[0]
        inv = p.get('inventory', [])
        rrt = next((i for i in inv if i['name'] == 'Race Reroll Token'), None)

        if not rrt:
            await ctx.send(embed=discord.Embed(
                description="❌ You don't have a Race Reroll Token!\nBuy one from `!shop 2`",
                color=GOLD))
            return

        from main import RACE_POOL_REROLL, RACES

        new_race = random.choice(RACE_POOL_REROLL)
        stats = RACES[new_race]
        unspent = p.get('unspent_points', 0)

        str_spent = p.get('str', 0) - stats['str']
        mag_spent = p.get('mag', 0) - stats['mag']
        def_spent = p.get('def', 0) - stats['def']
        hp_spent = p.get('hp', 0) - stats['hp']

        total_returned = max(0, str_spent) + max(0, mag_spent) + max(0, def_spent) + max(0, hp_spent)
        new_unspent = unspent + total_returned

        new_inv = [i for i in inv if i['uid'] != rrt['uid']]

        players.update({
            'race': new_race,
            'hp': stats['hp'],
            'str': stats['str'],
            'mag': stats['mag'],
            'def': stats['def'],
            'unspent_points': new_unspent,
            'inventory': new_inv
        }, Player.id == user_id)

        embed = discord.Embed(
            title="🎲 Race Reroll!",
            description=f"Your new race is **{new_race}** `{stats['rarity']}`!",
            color=GOLD)
        embed.add_field(name="❤️ HP", value=f"`{stats['hp']}`", inline=True)
        embed.add_field(name="⚔️ STR", value=f"`{stats['str']}`", inline=True)
        embed.add_field(name="✨ MAG", value=f"`{stats['mag']}`", inline=True)
        embed.add_field(name="🛡️ DEF", value=f"`{stats['def']}`", inline=True)
        if total_returned > 0:
            embed.add_field(
                name="💡 Stat Points Returned",
                value=f"`{total_returned}` points returned to unspent!",
                inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="items")
    async def items(self, ctx):
        embed = discord.Embed(title="📦 Nexworld Item Compendium", color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(
            name="🗺️ Explore Drops — `!explore`",
            value="**Common:** Slime Jelly, Sharp Thorn, Torn Fur, Weak Venom Pod, Luminescent Spores, Ancient Bone, Putrid Flesh\n"
                  "**Uncommon:** Ectoplasm, Iron Ore Fragment, Contaminated Tooth, Dark Cloth, Fire Scale, Sulfuric Ash, Ember Core, Winter Pelt (Uncommon)",
            inline=False)
        embed.add_field(
            name="⚔️ Battle Drops — win fights",
            value="Rare → Celestial drops depending on the arc you're in. Drop chance 30% (55% with Luck Potion).",
            inline=False)
        embed.add_field(
            name="🏴‍☠️ Raid Drops — win raids",
            value="**Epic/Legendary:** Void Shard, Chaos Crystal, Storm Feather, Dragon Scale Fragment, Soul Ember, Abyss Rune",
            inline=False)
        embed.add_field(
            name="🏪 Shop 1 — Nexcoins `!shop 1`",
            value="Weapons & Armor (Rare → Legendary), HP Potions, EXP Boost Potion, Luck Potion, Item Pack",
            inline=False)
        embed.add_field(
            name="✨ Shop 2 — Starshards `!shop 2`",
            value="Weapons & Armor (Mythic → Godly), Race Reroll Token, Pet Pack",
            inline=False)
        embed.add_field(
            name="🐾 Pets — Daily Shop & Pet Pack",
            value="Common → Divine pets. Use `!shop` → Daily Shop or `!buy 2 10` for Pet Pack.",
            inline=False)
        embed.add_field(
            name="🎉 Event Items — Coming Soon!",
            value="Limited items exclusive to special events. Stay tuned!",
            inline=False)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.add_field(name="💡 Tip", value="Use `!info <item name>` to see any item's full stats!", inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="info")
    async def info(self, ctx, *, item_name: str = None):
        if not item_name:
            await ctx.send(embed=discord.Embed(description="Usage: `!info <item name>`\nExample: `!info Excalibur`", color=GOLD))
            return
        query = item_name.lower()
        all_items = (
            [dict(i, source="Shop 1") for i in NEXCOIN_SHOP] +
            [dict(i, source="Shop 2") for i in SS_SHOP] +
            [dict(i, source="Pet Pack / Daily Shop") for i in PETS]
        )
        found = next((i for i in all_items if i['name'].lower() == query), None)
        if not found:
            found = next((i for i in all_items if query in i['name'].lower()), None)
        if not found:
            await ctx.send(embed=discord.Embed(
                description=f"❌ No item found matching **{item_name}**.\nTry `!items` for the full list.",
                color=GOLD))
            return
        rarity_icons = {"Common": "⚪", "Uncommon": "🟢", "Rare": "🔵", "Epic": "🟣",
                        "Legendary": "🟠", "Mythic": "🔴", "Divine": "🟡", "Godly": "🔱",
                        "Celestial": "💠", "Special": "✨"}
        icon = rarity_icons.get(found.get('rarity', ''), '❓')
        embed = discord.Embed(
            title=f"{icon} {found['name']}",
            description=found.get('description', '—'),
            color=GOLD)
        embed.add_field(name="Rarity", value=f"`{found.get('rarity', '—')}`", inline=True)
        embed.add_field(name="Type", value=f"`{found.get('type', '—')}`", inline=True)
        if found.get('source'):
            embed.add_field(name="Obtained From", value=found['source'], inline=True)
        stats = found.get('stats', {})
        if stats:
            stat_lines = []
            if stats.get('hp'):  stat_lines.append(f"❤️ HP: `+{stats['hp']}`")
            if stats.get('str'): stat_lines.append(f"⚔️ ATK: `+{stats['str']}`")
            if stats.get('mag'): stat_lines.append(f"✨ MAG: `+{stats['mag']}`")
            if stats.get('def'): stat_lines.append(f"🛡️ DEF: `+{stats['def']}`")
            embed.add_field(name="Stat Boosts", value="\n".join(stat_lines), inline=False)
        price = found.get('price')
        if price:
            currency = "Starshards" if found.get('source') == "Shop 2" else "Nexcoins"
            embed.add_field(name="Price", value=f"`{price:,}` {currency}", inline=True)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        await ctx.send(embed=embed)

    @commands.command(name="usebuff")
    async def use_item(self, ctx, uid: str = None):
        if not uid:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!usebuff <item_id>`\nUsable items: **EXP Boost Potion**, **Luck Potion**",
                color=GOLD))
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
        now = time.time()
        if item.get('name') == 'EXP Boost Potion':
            if now < p.get('buff_exp_boost_until', 0):
                remaining = int(p['buff_exp_boost_until'] - now)
                await ctx.send(embed=discord.Embed(
                    description=f"⚠️ EXP Boost is already active!\nExpires in `{remaining}s`",
                    color=GOLD))
                return
            inv.remove(item)
            players.update({'buff_exp_boost_until': now + 300, 'inventory': inv}, Player.id == u�ser_id)
            embed = discord.Embed(title="⚗️ EXP Boost Active!", color=GOLD)
            embed.add_field(name="Effect", value="EXP gain **doubled** ✨", inline=True)
            embed.add_field(name="Duration", value="`5 minutes`", inline=True)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed)
        elif item.get('name') == 'Luck Potion':
            if now < p.get('buff_luck_until', 0):
                remaining = int(p['buff_luck_until'] - now)
                await ctx.send(embed=discord.Embed(
                    description=f"⚠️ Luck Boost is already active!\nExpires in `{remaining}s`",
                    color=GOLD))
                return
            inv.remove(item)
            players.update({'buff_luck_until': now + 300, 'inventory': inv}, Player.id == user_id)
            embed = discord.Embed(title="🍀 Luck Boost Active!", color=GOLD)
            embed.add_field(name="Effect", value="Drop luck & pet pack rarity **boosted** 🍀", inline=True)
            embed.add_field(name="Duration", value="`5 minutes`", inline=True)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed)
        elif item.get('name') == 'DEF Boost Potion':
            if now < p.get('buff_def_boost_until', 0):
                remaining = int(p['buff_def_boost_until'] - now)
                await ctx.send(embed=discord.Embed(
                    description=f"⚠️ DEF Boost is already active!\nExpires in `{remaining}s`",
                    color=GOLD))
                return
            inv.remove(item)
            players.update({'buff_def_boost_until': now + 300, 'inventory': inv}, Player.id == user_id)
            embed = discord.Embed(title="🛡️ DEF Boost Active!", color=GOLD)
            embed.add_field(name="Effect", value="+100 DEF for 5 minutes", inline=True)
            embed.add_field(name="Duration", value="`5 minutes`", inline=True)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed)
        elif item.get('name') == 'STR Boost Potion':
            if now < p.get('buff_str_boost_until', 0):
                remaining = int(p['buff_str_boost_until'] - now)
                await ctx.send(embed=discord.Embed(
                    description=f"⚠️ STR Boost is already active!\nExpires in `{remaining}s`",
                    color=GOLD))
                return
            inv.remove(item)
            players.update({'buff_str_boost_until': now + 300, 'inventory': inv}, Player.id == user_id)
            embed = discord.Embed(title="⚔️ STR Boost Active!", color=GOLD)
            embed.add_field(name="Effect", value="+100 STR & +100 MAG for 5 minutes", inline=True)
            embed.add_field(name="Duration", value="`5 minutes`", inline=True)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=discord.Embed(
                description=f"❌ **{item.get('name', uid)}** can't be activated with `!usebuff`!\nUsable items: **EXP Boost Potion**, **Luck Potion**, **DEF Boost Potion**, **STR Boost Potion**",
                color=GOLD))

async def setup(bot):
    await bot.add_cog(Shop(bot))