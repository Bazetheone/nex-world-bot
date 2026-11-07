import discord
from discord.ext import commands
from db import players, Player
from rarity import rarity_icon
from stats import derive_item_pct

GOLD = 0xFFD700
NC_ICON = "<:nexcoin:1530890951437058128>"
SS_ICON = "<:starshard:1533458421037138020>"
PER_PAGE = 8
GEAR_TYPES = ('weapon', 'armor', 'head_armor', 'body_armor')
LABELS = {'hp': 'HP', 'str': 'STR', 'def': 'DEF', 'mag': 'Magic Power'}

CATEGORIES = {
    'all': ('All Items', None, '📦'),
    'weapon': ('Weapons', ('weapon',), '⚔️'),
    'armor': ('Body Armor', ('armor', 'body_armor'), '🛡️'),
    'head': ('Head Armor', ('head_armor',), '🪖'),
    'potion': ('Potions & Consumables', ('buff', 'consumable'), '🧴'),
}


def _shop_items(which, category):
    from cogs.shop import NEXCOIN_SHOP, SS_SHOP
    items = list(NEXCOIN_SHOP if which == 'nexcoin' else SS_SHOP)
    types = CATEGORIES[category][1]
    if types:
        items = [i for i in items if i.get('type') in types]
    return sorted(items, key=lambda i: i.get('id', 0))


def _item_line(item, which):
    from cogs.shop import RACE_AFFINITY
    icon = rarity_icon(item.get('rarity'))
    if item.get('type') in GEAR_TYPES:
        pct = derive_item_pct(item)
        info = ", ".join(f"+{v:g}% {LABELS[k]}" for k, v in pct.items()) or "-"
    else:
        info = str(item.get('description', '')).replace('`', '')
        if len(info) > 60:
            info = info[:57] + "..."
    race = RACE_AFFINITY.get(item.get('name'))
    tag = f" `[{race}]`" if race else ""
    cur = NC_ICON if which == 'nexcoin' else SS_ICON
    return f"`{item['id']:>2}` {icon} **{item['name']}**{tag}\n┗ {info} • {cur} `{item['price']:,}`"


def build_browse_embed(which, page, category, user_id):
    items = _shop_items(which, category)
    total_pages = max(1, (len(items) + PER_PAGE - 1) // PER_PAGE)
    page = max(1, min(page, total_pages))
    chunk = items[(page - 1) * PER_PAGE: page * PER_PAGE]
    found = players.search(Player.id == user_id)
    p = found[0] if found else {}
    if which == 'nexcoin':
        icon, name, bal, cmd = NC_ICON, "NEXCOIN SHOP", p.get('nexcoins', 0), "!buy 1 <id>"
    else:
        icon, name, bal, cmd = SS_ICON, "STARSHARD SHOP", p.get('starshards', 0), "!buy 2 <id>"
    lines = "\n".join(_item_line(i, which) for i in chunk) or "Nothing here yet."
    desc = (f"{icon} **Balance:** `{bal:,}`\n"
            f"**Filter:** {CATEGORIES[category][0]}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n{lines}")
    embed = discord.Embed(title=f"{icon} {name} — Page {page}/{total_pages}", description=desc, color=GOLD)
    embed.set_footer(text=f"Buy with {cmd} • Nexworld RPG")
    return embed, page


class CategorySelect(discord.ui.Select):
    def __init__(self, view_ref):
        self.view_ref = view_ref
        options = [discord.SelectOption(label=v[0], value=k, emoji=v[2]) for k, v in CATEGORIES.items()]
        super().__init__(placeholder="🔎 Filter items", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        v = self.view_ref
        v.category = self.values[0]
        v.page = 1
        await interaction.response.edit_message(embed=v.make_embed(), view=v)


class BrowseView(discord.ui.View):
    def __init__(self, ctx, which, category='all', page=1):
        super().__init__(timeout=90)
        self.ctx = ctx
        self.which = which
        self.category = category
        self.page = page
        self.add_item(CategorySelect(self))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return False
        return True

    def make_embed(self):
        embed, self.page = build_browse_embed(self.which, self.page, self.category, str(self.ctx.author.id))
        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.grey, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.grey, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="🔙 Menu", style=discord.ButtonStyle.blurple, row=0)
    async def menu_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.shop import build_daily_shop_embed
        await interaction.response.edit_message(embed=build_daily_shop_embed(), view=MenuView(self.ctx))
        self.stop()

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.red, row=0)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(description="Shop closed.", color=GOLD), view=None)
        self.stop()


class MenuView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=90)
        self.ctx = ctx

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your shop!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Nexcoin Shop", style=discord.ButtonStyle.blurple, emoji=NC_ICON)
    async def nexcoin_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BrowseView(self.ctx, 'nexcoin')
        await interaction.response.edit_message(embed=view.make_embed(), view=view)
        self.stop()

    @discord.ui.button(label="Starshard Shop", style=discord.ButtonStyle.green, emoji=SS_ICON)
    async def ss_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = BrowseView(self.ctx, 'starshard')
        await interaction.response.edit_message(embed=view.make_embed(), view=view)
        self.stop()

    @discord.ui.button(label="🛍️ Daily Shop", style=discord.ButtonStyle.grey)
    async def daily_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        from cogs.shop import build_daily_shop_embed
        await interaction.response.edit_message(embed=build_daily_shop_embed(), view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.red)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(description="Shop closed.", color=GOLD), view=None)
        self.stop()


class ShopUI(commands.Cog, name="ShopUI"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="shop")
    async def shop(self, ctx, shop_num: int = None):
        found = players.search(Player.id == str(ctx.author.id))
        if not found:
            await ctx.send(embed=discord.Embed(
                description="❌ You haven't started yet! Use `!start` to begin.", color=GOLD))
            return
        if shop_num == 1:
            view = BrowseView(ctx, 'nexcoin')
            await ctx.send(embed=view.make_embed(), view=view)
        elif shop_num == 2:
            view = BrowseView(ctx, 'starshard')
            await ctx.send(embed=view.make_embed(), view=view)
        else:
            from cogs.shop import build_daily_shop_embed
            await ctx.send(embed=build_daily_shop_embed(), view=MenuView(ctx))

GALLERY_PER_PAGE = 8
GALLERY_CATS = {
    'weapon': ('Weapons', '⚔️', ('weapon',)),
    'armor': ('Body Armor', '🛡️', ('armor', 'body_armor')),
    'head': ('Head Armor', '🪖', ('head_armor',)),
    'pet': ('Pets', '🐾', None),
    'potion': ('Potions & Consumables', '🧴', ('buff', 'consumable')),
    'drops': ('Materials & Drops', '🧪', None),
}
RAID_DROP_NAMES = ["Void Shard", "Chaos Crystal", "Storm Feather",
                   "Dragon Scale Fragment", "Soul Ember", "Abyss Rune"]


def _pack_pool():
    try:
        from cogs.pack import ITEM_PACK_POOL
        return ITEM_PACK_POOL
    except Exception:
        return {}


def gallery_entries(cat):
    from rarity import rarity_rank
    from cogs.shop import NEXCOIN_SHOP, SS_SHOP, PETS, RACE_AFFINITY
    out = []
    if cat in ('weapon', 'armor', 'head', 'potion'):
        types = GALLERY_CATS[cat][2]
        seen = {}
        for source, lst in (("Shop 1", NEXCOIN_SHOP), ("Shop 2", SS_SHOP)):
            for it in lst:
                if it.get('type') in types:
                    seen.setdefault(it['name'], [it, []])[1].append(source)
        for rar, lst in _pack_pool().items():
            for it in lst:
                if it.get('type') in types:
                    entry = seen.setdefault(it['name'], [dict(it, rarity=rar), []])
                    if 'Item Pack' not in entry[1]:
                        entry[1].append('Item Pack')
        for name, (it, sources) in seen.items():
            race = RACE_AFFINITY.get(name)
            tag = f" `[{race}]`" if race else ""
            if cat == 'potion':
                info = str(it.get('description', '')).replace('`', '')
                if len(info) > 70:
                    info = info[:67] + "..."
            else:
                pct = derive_item_pct(it)
                info = ", ".join(f"+{v:g}% {LABELS[k]}" for k, v in pct.items()) or "-"
            text = f"{rarity_icon(it.get('rarity'))} **{name}**{tag}\n┗ {info} • 📍 {', '.join(sources)}"
            out.append((rarity_rank(it.get('rarity')), name, text))
    elif cat == 'pet':
        for it in PETS:
            race = RACE_AFFINITY.get(it['name'])
            tag = f" `[{race}]`" if race else ""
            pct = derive_item_pct(it, is_pet=True)
            info = ", ".join(f"+{v:g}% {LABELS[k]}" for k, v in pct.items()) or "-"
            passive = f" • 🌟 {it['passive']}" if it.get('passive') else ""
            text = f"{rarity_icon(it.get('rarity'))} **{it['name']}**{tag}\n┗ {info}{passive} • 📍 Pet Pack / Daily Shop"
            out.append((rarity_rank(it.get('rarity')), it['name'], text))
    else:
        seen = {}
        try:
            from main import ARCS
            for arc_num, arc in ARCS.items():
                for e in arc.get('enemies', []):
                    d = e.get('drop')
                    if d and d not in seen:
                        seen[d] = (e.get('rarity', 'Common'), f"Arc {arc_num} battles")
        except Exception:
            pass
        try:
            from cogs.economy import EXPLORE_ITEMS
            for it in EXPLORE_ITEMS:
                seen.setdefault(it['name'], (it.get('rarity', 'Common'), 'Explore'))
        except Exception:
            pass
        for n in RAID_DROP_NAMES:
            seen.setdefault(n, ('Epic', 'Raids'))
        for n, (rar, where) in seen.items():
            out.append((rarity_rank(rar), n, f"{rarity_icon(rar)} **{n}**\n┗ 📍 {where}"))
    out.sort(key=lambda x: (x[0], x[1]))
    return [x[2] for x in out]


class GallerySelect(discord.ui.Select):
    def __init__(self, view_ref):
        self.view_ref = view_ref
        options = [discord.SelectOption(label=v[0], value=k, emoji=v[1]) for k, v in GALLERY_CATS.items()]
        super().__init__(placeholder="📚 Browse a category", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        v = self.view_ref
        v.category = self.values[0]
        v.page = 1
        await interaction.response.edit_message(embed=v.make_embed(), view=v)


class GalleryView(discord.ui.View):
    def __init__(self, ctx, category='weapon'):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.category = category
        self.page = 1
        self.add_item(GallerySelect(self))

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your gallery!", ephemeral=True)
            return False
        return True

    def make_embed(self):
        entries = gallery_entries(self.category)
        total_pages = max(1, (len(entries) + GALLERY_PER_PAGE - 1) // GALLERY_PER_PAGE)
        self.page = max(1, min(self.page, total_pages))
        chunk = entries[(self.page - 1) * GALLERY_PER_PAGE: self.page * GALLERY_PER_PAGE]
        name, emoji = GALLERY_CATS[self.category][0], GALLERY_CATS[self.category][1]
        embed = discord.Embed(
            title=f"{emoji} Item Gallery — {name}",
            description="\n".join(chunk) or "Nothing here yet.",
            color=GOLD)
        embed.set_footer(text=f"Page {self.page}/{total_pages} • {len(entries)} entries • !info <name> for full details")
        return embed

    @discord.ui.button(label="◀", style=discord.ButtonStyle.grey, row=0)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = max(1, self.page - 1)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.grey, row=0)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.red, row=0)
    async def close_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(
            embed=discord.Embed(description="Gallery closed.", color=GOLD), view=None)
        self.stop()


class Gallery(commands.Cog, name="Gallery"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="items", aliases=["gallery", "index"])
    async def items(self, ctx):
        view = GalleryView(ctx)
        await ctx.send(embed=view.make_embed(), view=view)


async def setup(bot):
    for name in ('shop', 'items'):
        if bot.get_command(name):
            bot.remove_command(name)
    await bot.add_cog(ShopUI(bot))
    await bot.add_cog(Gallery(bot))
