import discord
from discord.ext import commands
from db import players, Player
import random
import asyncio
import time

GOLD = 0xFFD700

RARITY_ICONS = {
    "Common": "⚪", "Uncommon": "🟢", "Rare": "🔵",
    "Epic": "🟣", "Legendary": "🟠", "Mythic": "🔴",
    "Divine": "🟡", "Celestial": "💠"
}

active_battles = set()

def exp_required(level):
    return int(100 * (1.5 ** (level - 1)))

def calculate_damage(atk, def_stat):
    base = max(1, atk - def_stat // 2)
    return int(base * random.uniform(0.85, 1.15))

def get_skill_name(race, skill_index, level):
    from main import RACE_SKILLS
    skill = RACE_SKILLS[race]["skills"][skill_index]
    for i in range(len(skill["evo_levels"]) - 1, -1, -1):
        if level >= skill["evo_levels"][i]:
            return skill["evolutions"][i]
    return skill["evolutions"][0]

def get_stat_increase(level):
    from main import get_stat_increase as gsi
    return gsi(level)

def apply_level_up(p, user_id):
    current_exp = p.get('exp', 0)
    current_level = p.get('level', 1)
    leveled_up = False
    old_level = current_level
    hp = p.get('hp', 100)
    str_ = p.get('str', 10)
    mag = p.get('mag', 10)
    def_ = p.get('def', 10)

    while current_exp >= exp_required(current_level):
        current_exp -= exp_required(current_level)
        current_level += 1
        increase = get_stat_increase(current_level)
        hp += increase['hp']
        str_ += increase['str']
        mag += increase['mag']
        def_ += increase['def']
        leveled_up = True

    if leveled_up:
        players.update({
            'exp': current_exp,
            'level': current_level,
            'hp': hp,
            'str': str_,
            'mag': mag,
            'def': def_
        }, Player.id == user_id)

    return leveled_up, old_level, current_level

class BattleView(discord.ui.View):
    def __init__(self, ctx, player_data, enemy, arc_num, enemy_num):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.user_id = str(ctx.author.id)
        self.player_data = player_data
        self.enemy = enemy
        self.arc_num = arc_num
        self.enemy_num = enemy_num
        self.player_hp = player_data['hp']
        self.enemy_hp = enemy['hp']
        self.skill_uses = 0
        self.special_available = True
        self.battle_ended = False
        self.turn = 1
        self.message = None

        from main import RACE_SKILLS
        race = player_data['race']
        level = player_data.get('level', 1)
        special = RACE_SKILLS[race]['special']

        s1 = get_skill_name(race, 0, level)
        s2 = get_skill_name(race, 1, level)
        s3 = get_skill_name(race, 2, level)
        s4 = get_skill_name(race, 3, level)
        sp = special['name'] if level >= special['unlock_level'] else "🔒 Special"

        self.children[0].label = s1
        self.children[1].label = s2
        self.children[2].label = s3
        self.children[3].label = s4
        self.children[4].label = sp
        self.children[4].disabled = not (self.special_available and level >= special['unlock_level'])

    def stop(self):
        active_battles.discard(self.user_id)
        super().stop()

    async def on_timeout(self):
        active_battles.discard(self.user_id)
        if self.message:
            try:
                await self.message.edit(
                    embed=discord.Embed(title="⏰ Battle Timed Out!", description="You took too long to act!", color=GOLD),
                    view=None)
            except Exception:
                pass

    def get_hp_bar(self, current, maximum, length=10):
        filled = max(0, min(length, int((current / maximum) * length)))
        return f"`[{'█' * filled}{'░' * (length - filled)}]` {current:,}/{maximum:,}"

    async def get_embed(self, result_text=""):
        embed = discord.Embed(
            title=f"⚔️ {self.ctx.author.name} vs {self.enemy['name']}",
            color=GOLD)
        embed.add_field(
            name=f"👤 {self.ctx.author.name}",
            value=f"❤️ {self.get_hp_bar(self.player_hp, self.player_data['hp'])}",
            inline=False)
        embed.add_field(
            name=f"{RARITY_ICONS.get(self.enemy['rarity'], '⚪')} {self.enemy['name']} `{self.enemy['rarity']}`",
            value=f"❤️ {self.get_hp_bar(self.enemy_hp, self.enemy['hp'])}",
            inline=False)
        embed.add_field(name="🔄 Turn", value=f"`{self.turn}`", inline=True)
        embed.add_field(name="⚡ Skill Uses", value=f"`{self.skill_uses}`", inline=True)
        if result_text:
            embed.add_field(name="📋 Result", value=result_text, inline=False)
        embed.set_footer(text="Nexworld RPG • Your fate has been decided")
        return embed

    async def check_user(self, interaction):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("This isn't your battle!", ephemeral=True)
            return False
        return True

    async def disable_all(self):
        for child in self.children:
            child.disabled = True

    @discord.ui.button(label="Skill 1", style=discord.ButtonStyle.blurple, row=0)
    async def skill1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_user(interaction) or self.battle_ended:
            return
        await self.use_skill(interaction, 0)

    @discord.ui.button(label="Skill 2", style=discord.ButtonStyle.blurple, row=0)
    async def skill2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_user(interaction) or self.battle_ended:
            return
        await self.use_skill(interaction, 1)

    @discord.ui.button(label="Skill 3", style=discord.ButtonStyle.blurple, row=0)
    async def skill3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_user(interaction) or self.battle_ended:
            return
        await self.use_skill(interaction, 2)

    @discord.ui.button(label="Skill 4", style=discord.ButtonStyle.blurple, row=1)
    async def skill4(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_user(interaction) or self.battle_ended:
            return
        await self.use_skill(interaction, 3)

    @discord.ui.button(label="Special", style=discord.ButtonStyle.green, row=1)
    async def special_move(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_user(interaction) or self.battle_ended:
            return

        from main import RACE_SKILLS
        race = self.player_data['race']
        level = self.player_data.get('level', 1)
        special = RACE_SKILLS[race]['special']

        if level < special['unlock_level']:
            await interaction.response.send_message(f"Unlocks at level {special['unlock_level']}!", ephemeral=True)
            return
        if not self.special_available:
            await interaction.response.send_message("Not ready! Use skills 2 more times.", ephemeral=True)
            return

        now = time.time()
        str_bonus_sp = 100 if now < self.player_data.get('buff_str_boost_until', 0) else 0
        def_bonus_sp = 100 if now < self.player_data.get('buff_def_boost_until', 0) else 0
        best_atk = max(self.player_data['str'] + str_bonus_sp, self.player_data['mag'] + str_bonus_sp)
        dmg = calculate_damage(int(best_atk * 2.5), self.enemy['def'] // 2)
        self.enemy_hp -= dmg
        self.special_available = False
        self.skill_uses = 0

        self.children[4].disabled = True
        result = f"💫 **{special['name']}** dealt **{dmg:,}** MASSIVE damage!"

        if self.enemy_hp <= 0:
            self.enemy_hp = 0
            self.battle_ended = True
            await self.disable_all()
            await interaction.response.edit_message(embed=await self.get_embed(result), view=self)
            await self.end_battle(interaction, won=True)
            return

        enemy_dmg = calculate_damage(self.enemy['atk'], self.player_data['def'] + def_bonus_sp)
        self.player_hp -= enemy_dmg
        result += f"\n{self.enemy['name']} hit back for **{enemy_dmg:,}**!"
        self.turn += 1

        if self.player_hp <= 0:
            self.player_hp = 0
            self.battle_ended = True
            await self.disable_all()
            await interaction.response.edit_message(embed=await self.get_embed(result), view=self)
            await self.end_battle(interaction, won=False)
            return

        await interaction.response.edit_message(embed=await self.get_embed(result), view=self)

    @discord.ui.button(label="🧪 Potion", style=discord.ButtonStyle.grey, row=2)
    async def use_potion(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_user(interaction) or self.battle_ended:
            return

        user_id = str(self.ctx.author.id)
        fresh = players.search(Player.id == user_id)
        if not fresh:
            return
        inv = fresh[0].get('inventory', [])

        potion_priority = ["Large HP Potion", "Medium HP Potion", "Small HP Potion"]
        heal_pct = {"Small HP Potion": 0.15, "Medium HP Potion": 0.30, "Large HP Potion": 0.50}

        used = None
        for pname in potion_priority:
            for item in inv:
                if item.get('name') == pname:
                    used = item
                    break
            if used:
                break

        if not used:
            await interaction.response.send_message("❌ No HP potions in your inventory!", ephemeral=True)
            return

        inv.remove(used)
        players.update({'inventory': inv}, Player.id == user_id)

        max_hp = self.player_data['hp']
        heal = int(max_hp * heal_pct[used['name']])
        self.player_hp = min(max_hp, self.player_hp + heal)

        result = f"🧪 Used **{used['name']}**! Restored **{heal:,}** HP!"

        now2 = time.time()
        def_bonus_pt = 100 if now2 < self.player_data.get('buff_def_boost_until', 0) else 0
        enemy_dmg = calculate_damage(self.enemy['atk'], self.player_data['def'] + def_bonus_pt)
        self.player_hp -= enemy_dmg
        result += f"\n{self.enemy['name']} hit back for **{enemy_dmg:,}**!"
        self.turn += 1

        if self.player_hp <= 0:
            self.player_hp = 0
            self.battle_ended = True
            await self.disable_all()
            await interaction.response.edit_message(embed=await self.get_embed(result), view=self)
            await self.end_battle(interaction, won=False)
            return

        await interaction.response.edit_message(embed=await self.get_embed(result), view=self)

    @discord.ui.button(label="🏃 Flee", style=discord.ButtonStyle.red, row=2)
    async def flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_user(interaction) or self.battle_ended:
            return
        self.battle_ended = True
        await self.disable_all()
        await interaction.response.edit_message(
            embed=discord.Embed(title="🏃 Fled!", description="You escaped. No rewards.", color=GOLD),
            view=self)
        self.stop()

    async def use_skill(self, interaction, skill_index):
        now = time.time()
        str_bonus = 100 if now < self.player_data.get('buff_str_boost_until', 0) else 0
        def_bonus = 100 if now < self.player_data.get('buff_def_boost_until', 0) else 0
        best_atk = max(self.player_data['str'] + str_bonus, self.player_data['mag'] + str_bonus)
        dmg = calculate_damage(int(best_atk * 1.4), self.enemy['def'])
        self.enemy_hp -= dmg
        self.skill_uses += 1

        skill_name = get_skill_name(self.player_data['race'], skill_index, self.player_data.get('level', 1))

        if not self.special_available and self.skill_uses >= 2:
            self.special_available = True
            from main import RACE_SKILLS
            race = self.player_data['race']
            level = self.player_data.get('level', 1)
            special = RACE_SKILLS[race]['special']
            if level >= special['unlock_level']:
                self.children[4].disabled = False

        result = f"✨ **{skill_name}** dealt **{dmg:,}** damage!"

        if self.enemy_hp <= 0:
            self.enemy_hp = 0
            self.battle_ended = True
            await self.disable_all()
            await interaction.response.edit_message(embed=await self.get_embed(result), view=self)
            await self.end_battle(interaction, won=True)
            return

        enemy_dmg = calculate_damage(self.enemy['atk'], self.player_data['def'] + def_bonus)
        self.player_hp -= enemy_dmg
        result += f"\n{self.enemy['name']} hit back for **{enemy_dmg:,}**!"
        self.turn += 1

        if self.player_hp <= 0:
            self.player_hp = 0
            self.battle_ended = True
            await self.disable_all()
            await interaction.response.edit_message(embed=await self.get_embed(result), view=self)
            await self.end_battle(interaction, won=False)
            return

        await interaction.response.edit_message(embed=await self.get_embed(result), view=self)

    async def end_battle(self, interaction, won):
        from main import ARCS
        user_id = str(self.ctx.author.id)
        p = players.search(Player.id == user_id)
        if not p:
            return
        p = p[0]

        if won:
            exp_gain = random.randint(*self.enemy['exp'])
            coins_gain = random.randint(*self.enemy['coins'])

            if time.time() < p.get('buff_exp_boost_until', 0):
                exp_gain = int(exp_gain * 2)

            new_exp = p.get('exp', 0) + exp_gain
            new_coins = p.get('nexcoins', 0) + coins_gain

            players.update({'exp': new_exp, 'nexcoins': new_coins}, Player.id == user_id)

            fresh_p = players.search(Player.id == user_id)[0]
            leveled_up, old_level, new_level = apply_level_up(fresh_p, user_id)

            arc_data = ARCS[self.arc_num]
            total_enemies = len(arc_data['enemies'])
            next_enemy = self.enemy_num + 1
            current_arc = self.arc_num
            arc_unlocked = False

            if next_enemy > total_enemies:
                next_arc = self.arc_num + 1
                if next_arc in ARCS:
                    current_arc = next_arc
                    next_enemy = 1
                    arc_unlocked = True

            if self.enemy_num >= p.get('current_enemy', 1) and self.arc_num == p.get('current_arc', 1):
                players.update({'current_arc': current_arc, 'current_enemy': next_enemy}, Player.id == user_id)

            item_drop = None
            drop_chance = 0.55 if time.time() < p.get('buff_luck_until', 0) else 0.3
            if random.random() < drop_chance:
                item_drop = self.enemy.get('drop')
                if item_drop:
                    fresh_p2 = players.search(Player.id == user_id)[0]
                    inv = fresh_p2.get('inventory', [])
                    drop_items = [i for i in inv if i['uid'].startswith('D')]
                    uid = f"D{str(len(drop_items) + 1).zfill(3)}"
                    inv.append({'uid': uid, 'name': item_drop, 'rarity': self.enemy['rarity'], 'type': 'drop'})
                    players.update({'inventory': inv}, Player.id == user_id)

            embed = discord.Embed(title=f"✅ Victory! {self.enemy['name']} defeated!", color=0x00FF00)
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
            embed.add_field(name="💰 Nexcoins", value=f"`+{coins_gain:,}`", inline=True)
            embed.add_field(name="🔮 EXP", value=f"`+{exp_gain:,}`", inline=True)

            if item_drop:
                embed.add_field(name="🎁 Drop!", value=f"**{item_drop}** `{self.enemy['rarity']}`", inline=False)

            if leveled_up:
                embed.add_field(
                    name="⬆️ LEVEL UP!",
                    value=f"**{old_level} → {new_level}**\nStats automatically increased!",
                    inline=False)

            if arc_unlocked:
                embed.add_field(
                    name="🔓 Arc Unlocked!",
                    value=f"**Arc {current_arc} — {ARCS[current_arc]['name']}** unlocked!\nUse `!arc {current_arc}`",
                    inline=False)
            else:
                embed.add_field(name="➡️ Next", value=f"`!battle {next_enemy}` for the next enemy!", inline=False)

            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await interaction.followup.send(embed=embed)

        else:
            consolation = random.randint(200, 300)
            new_coins = p.get('nexcoins', 0) + consolation
            players.update({'nexcoins': new_coins}, Player.id == user_id)

            embed = discord.Embed(title=f"💀 Defeated by {self.enemy['name']}!", color=0xFF0000)
            embed.add_field(name="💰 Consolation", value=f"`+{consolation:,}` Nexcoins for trying!", inline=False)
            embed.add_field(name="💡 Tip", value="Fight previous enemies to get stronger!", inline=False)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await interaction.followup.send(embed=embed)

        self.stop()

class Battle(commands.Cog, name="Battle"):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="arc")
    async def arc(self, ctx, arc_num: int = None):
        from main import ARCS
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)

        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Use `!start` to begin!", color=GOLD))
            return

        p = p[0]
        current_arc = p.get('current_arc', 1)

        if arc_num is None:
            embed = discord.Embed(title="🗺️ Nexworld — Arcs", color=GOLD)
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
            for num, arc_data in ARCS.items():
                status = "✅" if num <= current_arc else "🔒"
                lvl = arc_data['level_range']
                embed.add_field(
                    name=f"{status} Arc {num} — {arc_data['name']}",
                    value=f"Levels `{lvl[0]}-{lvl[1]}` • `{len(arc_data['enemies'])}` enemies",
                    inline=False)
            embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
            embed.set_footer(text="Use !arc <number> to view enemies • Nexworld RPG")
            await ctx.send(embed=embed)
            return

        if arc_num not in ARCS:
            await ctx.send(embed=discord.Embed(description=f"❌ Arc {arc_num} doesn't exist!", color=GOLD))
            return

        if arc_num > current_arc:
            await ctx.send(embed=discord.Embed(
                description=f"🔒 Arc {arc_num} locked! Complete Arc {arc_num - 1} first.",
                color=GOLD))
            return

        arc_data = ARCS[arc_num]
        current_enemy = p.get('current_enemy', 1) if arc_num == current_arc else len(arc_data['enemies']) + 1

        embed = discord.Embed(
            title=f"Arc {arc_num} — {arc_data['name']}",
            description=f"Level Range: `{arc_data['level_range'][0]}-{arc_data['level_range'][1]}`",
            color=GOLD)
        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)

        for enemy in arc_data['enemies']:
            if arc_num < current_arc or (arc_num == current_arc and enemy['id'] < current_enemy):
                status = "✅"
            elif arc_num == current_arc and enemy['id'] == current_enemy:
                status = "⚔️ Current"
            else:
                status = "🔒"
            embed.add_field(
                name=f"{status} {enemy['id']}. {enemy['name']} — {RARITY_ICONS.get(enemy['rarity'], '⚪')} `{enemy['rarity']}`",
                value=f"❤️ `{enemy['hp']:,}` • ⚔️ `{enemy['atk']:,}` • 🛡️ `{enemy['def']:,}` • 🎁 `{enemy['drop']}`",
                inline=False)

        embed.add_field(name="━━━━━━━━━━━━━━━━━━━━━━", value="** **", inline=False)
        embed.set_footer(text="Use !battle <number> to fight • Nexworld RPG")
        await ctx.send(embed=embed)

    @commands.command(name="battle")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def battle(self, ctx, enemy_num: int = None):
        from main import ARCS
        user_id = str(ctx.author.id)

        if user_id in active_battles:
            await ctx.send(embed=discord.Embed(
                description="❌ You're already in a battle! Finish your current fight first.",
                color=GOLD))
            return

        p = players.search(Player.id == user_id)

        if not p:
            await ctx.send(embed=discord.Embed(description="❌ Use `!start` to begin!", color=GOLD))
            return

        p = p[0]

        if enemy_num is None:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!battle <number>`\nCheck `!arc` for available enemies.",
                color=GOLD))
            return

        current_arc = p.get('current_arc', 1)
        current_enemy = p.get('current_enemy', 1)
        arc_data = ARCS.get(current_arc)

        if not arc_data:
            await ctx.send(embed=discord.Embed(description="❌ No arc found!", color=GOLD))
            return

        if enemy_num > current_enemy:
            await ctx.send(embed=discord.Embed(
                description=f"🔒 Enemy {enemy_num} locked! Defeat enemy {current_enemy} first.",
                color=GOLD))
            return

        enemy = next((e for e in arc_data['enemies'] if e['id'] == enemy_num), None)

        if not enemy:
            await ctx.send(embed=discord.Embed(
                description=f"❌ Enemy {enemy_num} not found!\nUse `!arc {current_arc}` to see enemies.",
                color=GOLD))
            return

        active_battles.add(user_id)
        view = BattleView(ctx, p, enemy, current_arc, enemy_num)
        embed = await view.get_embed()
        msg = await ctx.send(embed=embed, view=view)
        view.message = msg

async def setup(bot):
    await bot.add_cog(Battle(bot))