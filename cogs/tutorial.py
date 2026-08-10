import discord
from discord.ext import commands

GOLD = 0xFFD700

TUTORIAL_PAGES = [
    {
        "title": "🌌 Awakening",
        "text": (
            "*...Consciousness detected...*\n\n"
            "A voice echoes through the void, ancient and patient.\n\n"
            "\"Another soul has awakened. I am **The Guide** — I have watched countless "
            "adventurers take their first steps into Nexworld, and I will walk beside you "
            "until you're ready to walk alone.\"\n\n"
            "\"Don't worry if everything feels unfamiliar. We'll go through it together, "
            "one step at a time.\""
        )
    },
    {
        "title": "📜 Identity",
        "text": (
            "\"Every adventurer carries a Chronicle — a record of who they are.\"\n\n"
            "➡️ Type `!profile` (or `!pf`)\n\n"
            "\"There you'll always find your race, level, stats, Guild Rank, and equipment. "
            "Return to it often — it never lies.\""
        )
    },
    {
        "title": "🗺️ First Steps",
        "text": (
            "\"Power is never given... it is earned.\"\n\n"
            "➡️ Type `!explore` to venture out and gather loot and experience.\n"
            "➡️ Type `!guild board` to see quests posted by the Adventurer's Guild.\n\n"
            "\"The Guild rewards those who stay active. Visit the board often — its offerings change.\""
        )
    },
    {
        "title": "⚔️ Your First Battle",
        "text": (
            "\"A blade that never leaves its sheath will eventually rust.\"\n\n"
            "➡️ Type `!arc` to see the story arcs available to you.\n"
            "➡️ Type `!battle 1` to challenge the first enemy of your current arc.\n\n"
            "\"Victory rewards you with EXP. As it grows, so too will your strength.\""
        )
    },
    {
        "title": "🔮 Skills & Power",
        "text": (
            "\"Your race is not merely a title — it is part of who you are.\"\n\n"
            "➡️ Type `!skills` to see your racial abilities.\n\n"
            "\"Some strike with overwhelming force. Others heal, shield, or weaken a foe. "
            "As you level, your skills evolve and grow stronger. Master them, and they'll "
            "become your greatest allies.\""
        )
    },
    {
        "title": "📈 Growing Stronger",
        "text": (
            "\"Leveling grants you points to shape your own strength.\"\n\n"
            "➡️ Type `!points` to check your unspent points.\n"
            "➡️ Type `!assign <stat> <amount>` to spend them — choose from `hp`, `str`, `mag`, `def`.\n\n"
            "\"Build yourself as you see fit. A warrior of brute force, or a caster of ruin — "
            "the choice is yours.\""
        )
    },
    {
        "title": "🛡️ Equipment",
        "text": (
            "\"A warrior's strength is measured not only by skill, but by what they choose to wield.\"\n\n"
            "➡️ Type `!inventory` (or `!inv`) to view your items.\n"
            "➡️ Type `!ie <item id>` to equip an item, or `!iue <slot>` to unequip.\n\n"
            "\"Every piece of equipment carries an Affinity. When it resonates with your race, "
            "its true power is revealed. Mismatched gear still fights for you — just not with its full strength.\""
        )
    },
    {
        "title": "🏪 Commerce",
        "text": (
            "\"Not everything must be earned through battle.\"\n\n"
            "➡️ Type `!shop` to browse the merchant's wares.\n"
            "➡️ Type `!market` to buy and sell among fellow adventurers.\n"
            "➡️ Type `!pay @user <amount>` to send Nexcoins, or `!trade @user` to exchange items directly.\n\n"
            "\"The economy of Nexworld is shaped by its people. Spend wisely.\""
        )
    },
    {
        "title": "🤝 Community",
        "text": (
            "\"There comes a time when no adventurer stands alone.\"\n\n"
            "➡️ Type `!clan register <name>` to found a clan, or `!clan join <name>` to join one.\n"
            "➡️ Type `!fight @user` to challenge another adventurer to a duel.\n\n"
            "\"Find allies whose ambitions match your own — or build a legacy that others will follow.\""
        )
    },
    {
        "title": "🌍 The Wider World",
        "text": (
            "\"Beyond the horizon, far greater trials await.\"\n\n"
            "➡️ Type `!raid` to summon a raid boss alongside other adventurers.\n"
            "➡️ Type `!vote` to support Nexworld and earn Starshards, a rare and powerful currency.\n\n"
            "\"Some paths remain closed to beginners. When your strength is enough, the world itself "
            "will invite you forward.\""
        )
    },
    {
        "title": "✨ Farewell",
        "text": (
            "\"My duty ends here.\"\n\n"
            "\"From this moment onward, every victory, every defeat, every choice — belongs to you.\"\n\n"
            "\"Will your name become a legend, or be forgotten by history?\"\n\n"
            "\"Go. Nexworld awaits.\"\n\n"
            "🎉 **Tutorial Complete!** Use `!tutorial` anytime to revisit this guide."
        )
    },
]

class TutorialView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=180)
        self.ctx = ctx
        self.page = 0
        self._update_buttons()

    def _update_buttons(self):
        self.children[0].disabled = self.page == 0
        self.children[1].disabled = self.page == len(TUTORIAL_PAGES) - 1

    def build_embed(self):
        page = TUTORIAL_PAGES[self.page]
        embed = discord.Embed(title=page["title"], description=page["text"], color=GOLD)
        embed.set_footer(text=f"The Guide • Page {self.page + 1}/{len(TUTORIAL_PAGES)} • Nexworld RPG")
        return embed

    async def _check_user(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your tutorial!", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="◀ Previous", style=discord.ButtonStyle.grey)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user(interaction):
            return
        if self.page > 0:
            self.page -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="Next ▶", style=discord.ButtonStyle.grey)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._check_user(interaction):
            return
        if self.page < len(TUTORIAL_PAGES) - 1:
            self.page += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

class Tutorial(commands.Cog, name="Tutorial"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="tutorial")
    async def tutorial(self, ctx):
        view = TutorialView(ctx)
        await ctx.send(embed=view.build_embed(), view=view)

async def setup(bot):
    await bot.add_cog(Tutorial(bot))
