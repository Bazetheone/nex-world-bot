import discord
from discord.ext import commands
from tinydb import Query
from db import players, raids_table, Player
import random
import asyncio
import time

Raid = Query()

GOLD = 0xFFD700

BOSSES = [
    {"id": 1,  "name": "The Broodmother",          "tier": 1, "hp": 30000,   "atk": 1800,  "def": 500,   "passive": "Infestation",     "passive_desc": "Spawns a spider minion that deals extra damage"},
    {"id": 2,  "name": "Goblin King Grik",          "tier": 1, "hp": 40000,   "atk": 2200,  "def": 700,   "passive": "Coward's Command", "passive_desc": "Gains +30% DEF when HP falls below 50%"},
    {"id": 3,  "name": "Corrupted Oak Ent",         "tier": 1, "hp": 55000,   "atk": 1600,  "def": 1200,  "passive": "Deep Roots",       "passive_desc": "Regenerates 15% Max HP upon reaching 50%"},
    {"id": 4,  "name": "The Shadow Stalker",        "tier": 1, "hp": 30000,   "atk": 2800,  "def": 400,   "passive": "Flicker",          "passive_desc": "Gains 30% evasion when HP falls below 50%"},
    {"id": 5,  "name": "Arch-Necromancer Malakor",  "tier": 2, "hp": 100000,  "atk": 4500,  "def": 1200,  "passive": "Soul Feast",       "passive_desc": "Heals for 30% of damage dealt for the rest of the fight"},
    {"id": 6,  "name": "The Bloodless Executioner", "tier": 2, "hp": 140000,  "atk": 5500,  "def": 2000,  "passive": "Heavy Cleave",     "passive_desc": "Deals an extra 50% damage hit on activation"},
    {"id": 7,  "name": "Skeletal Titan",            "tier": 2, "hp": 180000,  "atk": 4000,  "def": 3000,  "passive": "Bone Armor",       "passive_desc": "Reduces your damage by 25% for the rest of the fight"},
    {"id": 8,  "name": "The Banshee Queen",         "tier": 2, "hp": 80000,   "atk": 6500,  "def": 1000,  "passive": "Screech",          "passive_desc": "Reduces your damage by 20% for the rest of the fight"},
    {"id": 9,  "name": "Infernal Wyrm",             "tier": 3, "hp": 300000,  "atk": 8000,  "def": 3000,  "passive": "Blazing Aura",     "passive_desc": "Ignites, dealing bonus fire damage each turn"},
    {"id": 10, "name": "Dreadlord of the Pit",      "tier": 3, "hp": 350000,  "atk": 10000, "def": 3500,  "passive": "Terror",           "passive_desc": "Reduces your damage by 15% for the rest of the fight"},
    {"id": 11, "name": "Empress of the Oasis",      "tier": 3, "hp": 250000,  "atk": 11000, "def": 2500,  "passive": "Mirage",           "passive_desc": "50% of your attacks hit a mirage and deal no damage"},
    {"id": 12, "name": "Colossus of Iron & Rust",   "tier": 3, "hp": 500000,  "atk": 7000,  "def": 6000,  "passive": "Unstoppable",      "passive_desc": "Immune to CC; deals an extra hit on activation"},
    {"id": 13, "name": "Frost-Giant Overlord",      "tier": 4, "hp": 600000,  "atk": 15000, "def": 7000,  "passive": "Permafrost",       "passive_desc": "Reduces your damage by 25% for the rest of the fight"},
    {"id": 14, "name": "The Ancient Phoenix",       "tier": 4, "hp": 600000,  "atk": 20000, "def": 5000,  "passive": "Rebirth",          "passive_desc": "Revives once with 30% HP upon first death"},
    {"id": 15, "name": "Serpent of the Depths",     "tier": 4, "hp": 700000,  "atk": 18000, "def": 9000,  "passive": "Tidal Shield",     "passive_desc": "Gains a shield worth 10% of max HP"},
    {"id": 16, "name": "The Silent Assassin Prime", "tier": 4, "hp": 600000,  "atk": 28000, "def": 4000,  "passive": "Expose Flaw",      "passive_desc": "Boss ATK increases by 50% for the rest of the fight"},
    {"id": 17, "name": "Void Emperor Zerath",       "tier": 5, "hp": 1500000, "atk": 45000, "def": 15000, "passive": "Nullification",    "passive_desc": "Clears your active buffs and deals a power strike"},
    {"id": 18, "name": "Time-Eater Chronos",        "tier": 5, "hp": 2000000, "atk": 55000, "def": 12000, "passive": "Time Loop",        "passive_desc": "Attacks twice for the rest of the fight"},
    {"id": 19, "name": "Nebula Dragon Bahamut",     "tier": 5, "hp": 3000000, "atk": 65000, "def": 20000, "passive": "Cosmic Collapse",  "passive_desc": "Deals catastrophic bonus damage on activation"},
    {"id": 20, "name": "The Genesis Architect",     "tier": 5, "hp": 5000000, "atk": 80000, "def": 40000, "passive": "Divine Order",     "passive_desc": "Immune to reduction effects; unleashes divine wrath"},
]

TIER_NAMES = {
    1: "Early Game",
    2: "Mid Game",
    3: "Elemental",
    4: "Late Game",
    5: "Godly"
}

active_raids = {}

def calculate_damage(atk, def_stat):
    base = max(atk // 5, atk - def_stat // 2)
    return max(1, int(base * random.uniform(0.85, 1.15)))

class RaidJoinView(discord.ui.View):
    def __init__(self, raid_data, spawner_id, channel):
        super().__init__(timeout=300)
        self.raid_data = raid_data
        self.spawner_id = spawner_id
        self.channel = channel
        self.players = []
        self.started = False
        self.message = None

    async def get_embed(self):
        boss = self.raid_data
        embed = discord.Embed(
            title=f"👹 Raid — {boss['name']}",
            description=f"**Passive:** {boss['passive']} — *{boss['passive_desc']}*",
            color=0xFF4444)
        embed.add_field(name="❤️ HP", value=f"`{boss['hp']:,}`", inline=True)
        embed.add_field(name="⚔️ ATK", value=f"`{boss['atk']:,}`", inline=True)
        embed.add_field(name="🛡️ DEF", value=f"`{boss['def']:,}`", inline=True)
        embed.add_field(name="🏆 Tier", value=f"`{TIER_NAMES[boss['tier']]}`", inline=True)
        embed.add_field(name="👥 Players", value=f"`{len(self.players)}/5`", inline=True)
        embed.add_field(name="⏰ Time", value="`5 minutes to join`", inline=True)

        if self.players:
            player_list = "\n".join([f"• {p['name']}" for p in self.players])
            embed.add_field(name="Players Joined", value=player_list, inline=False)

        embed.set_footer(text="Nexworld RPG • Click Enter Raid to join!")
        return embed

    @discord.ui.button(label="⚔️ Enter Raid", style=discord.ButtonStyle.green)
    async def enter_raid(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)

        if any(p['id'] == user_id for p in self.players):
            await interaction.response.send_message("You already joined this raid!", ephemeral=True)
            return

        if len(self.players) >= 5:
            await interaction.response.send_message("This raid is full! (Max 5 players)", ephemeral=True)
            return

        p = players.search(Player.id == user_id)
        if not p:
            await interaction.response.send_message("You haven't started yet! Use `!start` to begin.", ephemeral=True)
            return

        p = p[0]
        if p.get('banned', False):
            await interaction.response.send_message("You are banned from Nexworld!", ephemeral=True)
            return

        self.players.append({
            'id': user_id,
            'name': interaction.user.name,
            'hp': p['hp'],
            'str': p['str'],
            'mag': p['mag'],
            'def': p['def'],
            'level': p.get('level', 1),
            'race': p['race']
        })

        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(label="⚡ Force Start", style=discord.ButtonStyle.red)
    async def force_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        if str(interaction.user.id) != self.spawner_id:
            await interaction.response.send_message("Only the raid spawner can force start!", ephemeral=True)
            return

        if len(self.players) == 0:
            await interaction.response.send_message("At least 1 player must join first!", ephemeral=True)
            return

        self.started = True
        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(view=self)
        await self.start_raid()

    async def start_raid(self):
        boss = self.raid_data
        boss_hp = boss['hp']
        total_boss_hp = boss['hp']

        for i, player in enumerate(self.players):
            if boss_hp <= 0:
                break

            embed = discord.Embed(
                title=f"⚔️ {player['name']}'s Turn vs {boss['name']}",
                color=GOLD)
            embed.add_field(
                name=f"👹 {boss['name']}",
                value=f"❤️ HP: `{boss_hp:,}` / `{total_boss_hp:,}`",
                inline=False)
            embed.add_field(
                name=f"👤 {player['name']}",
                value=f"❤️ HP: `{player['hp']:,}`",
                inline=False)
            embed.add_field(
                name="Remaining Players",
                value=f"`{len(self.players) - i}` player(s) after this turn",
                inline=False)
            embed.set_footer(text="You have 2 minutes to act!")

            view = RaidBattleView(player, boss, boss_hp, total_boss_hp, i, self.players)
            msg = await self.channel.send(embed=embed, view=view)
            view.message = msg

            await view.wait()

            if view.boss_hp <= 0:
                await self.end_raid(won=True, remaining_players=self.players[i+1:], fighters=self.players[:i+1], damage_dealt=view.total_damage)
                return

            boss_hp = view.boss_hp

            if view.timed_out:
                await self.channel.send(f"⏰ {player['name']} ran out of time! Moving to next player...")

        await self.end_raid(won=False, remaining_players=[], fighters=self.players, damage_dealt=0)

    async def end_raid(self, won, remaining_players, fighters, damage_dealt):
        boss = self.raid_data

        if won:
            embed = discord.Embed(
                title=f"🎉 Raid Victory! {boss['name']} defeated!",
                color=0x00FF00)

            rewards_text = ""
            for player in fighters:
                coin_reward = random.randint(7000, 10000)
                exp_reward = random.randint(1000, 3000)
                p = players.search(Player.id == player['id'])
                if p:
                    p = p[0]
                    new_coins = p.get('nexcoins', 0) + coin_reward
                    new_exp = p.get('exp', 0) + exp_reward
                    players.update({'nexcoins': new_coins, 'exp': new_exp}, Player.id == player['id'])

                item_drop = None
                if random.random() < 0.5:
                    drop_rarities = ["Epic", "Epic", "Legendary"]
                    item_drop = random.choice(["Void Shard", "Chaos Crystal", "Storm Feather", "Dragon Scale Fragment", "Soul Ember", "Abyss Rune"])
                    rarity = random.choice(drop_rarities)
                    p_data = players.search(Player.id == player['id'])
                    if p_data:
                        inv = p_data[0].get('inventory', [])
                        uid = str(random.randint(100000, 999999))
                        inv.append({'uid': uid, 'name': item_drop, 'rarity': rarity, 'type': 'raid_drop'})
                        players.update({'inventory': inv}, Player.id == player['id'])

                rewards_text += f"**{player['name']}** — `{coin_reward:,}` Nexcoins, `{exp_reward:,}` EXP"
                if item_drop:
                    rewards_text += f", 🎁 {item_drop} `{rarity}`"
                rewards_text += "\n"

            for player in remaining_players:
                consolation = random.randint(7000, 10000)
                exp_reward = random.randint(500, 1000)
                p = players.search(Player.id == player['id'])
                if p:
                    p = p[0]
                    new_coins = p.get('nexcoins', 0) + consolation
                    new_exp = p.get('exp', 0) + exp_reward
                    players.update({'nexcoins': new_coins, 'exp': new_exp}, Player.id == player['id'])
                rewards_text += f"**{player['name']}** — `{consolation:,}` Nexcoins (supported), `{exp_reward:,}` EXP\n"

            embed.add_field(name="🏆 Rewards", value=rewards_text or "No rewards", inline=False)
            embed.set_footer(text="Nexworld RPG • Your fate has been decided")
            await self.channel.send(embed=embed)

        else:
            embed = discord.Embed(
                title=f"💀 Raid Failed! {boss['name']} was too powerful!",
                description="All players were defeated. No rewards earned.",
                color=0xFF0000)
            embed.set_footer(text="Nexworld RPG • Train harder and try again!")
            await self.channel.send(embed=embed)

class RaidBattleView(discord.ui.View):
    def __init__(self, player, boss, boss_hp, total_boss_hp, player_index, all_players):
        super().__init__(timeout=120)
        self.player = player
        self.boss = boss
        self.boss_hp = boss_hp
        self.total_boss_hp = total_boss_hp
        self.player_index = player_index
        self.all_players = all_players
        self.player_hp = player['hp']
        self.skill_uses = 0
        self.special_available = True
        self.total_damage = 0
        self.timed_out = False
        self.message = None
        self.turn = 1
        self.ability_used = False
        self.player_dmg_mult = 1.0
        self.boss_atk_mult = 1.0
        self.boss_evasion = 0.0
        self.player_evasion = 0.0
        self.boss_heals_on_hit = False
        self.boss_extra_fire = 0
        self.boss_attacks_twice = False
        self.boss_rebirth_ready = False
        self.boss_rebirth_used = False
        self.boss_shield = 0

        from main import RACE_SKILLS, get_skill_name
        race = player['race']
        level = player.get('level', 1)
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

    def get_hp_bar(self, current, maximum, length=10):
        filled = int((current / maximum) * length)
        filled = max(0, min(length, filled))
        bar = "█" * filled + "░" * (length - filled)
        return f"`[{bar}]` {current:,}/{maximum:,}"

    async def get_embed(self, result_text=""):
        embed = discord.Embed(
            title=f"⚔️ {self.player['name']} vs {self.boss['name']}",
            color=GOLD)
        embed.add_field(
            name=f"👹 {self.boss['name']}",
            value=f"❤️ {self.get_hp_bar(self.boss_hp, self.total_boss_hp)}",
            inline=False)
        embed.add_field(
            name=f"👤 {self.player['name']}",
            value=f"❤️ {self.get_hp_bar(self.player_hp, self.player['hp'])}",
            inline=False)
        embed.add_field(name="🔄 Turn", value=f"`{self.turn}`", inline=True)
        embed.add_field(name="⚡ Skill Uses", value=f"`{self.skill_uses}`", inline=True)
        if result_text:
            embed.add_field(name="📋 Result", value=result_text, inline=False)
        embed.set_footer(text="2 minutes to act! Nexworld RPG")
        return embed

    async def on_timeout(self):
        self.timed_out = True
        for child in self.children:
            child.disabled = True
        if self.message:
            await self.message.edit(view=self)
        self.stop()

    def _check_user(self, interaction):
        return str(interaction.user.id) == self.player['id']

    def _apply_ability(self):
        passive = self.boss.get('passive', '').lower()
        name = self.boss.get('passive', '?')
        text = f"\n\n⚠️ **{self.boss['name']}** activates **{name}!**"
        if 'infestation' in passive:
            extra = int(self.boss['atk'] * 0.4)
            self.player_hp -= extra
            text += f"\n🕷️ Spider minion strikes for **{extra:,}** damage!"
        elif "coward" in passive:
            self.boss_atk_mult = max(self.boss_atk_mult, 1.3)
            text += "\n🛡️ Goblin King cowers — boss gains +30% ATK!"
        elif "deep roots" in passive:
            heal = int(self.total_boss_hp * 0.15)
            self.boss_hp = min(self.total_boss_hp, self.boss_hp + heal)
            text += f"\n🌱 Boss regenerates **{heal:,}** HP!"
        elif "flicker" in passive:
            self.player_evasion = 0.3
            text += "\n💨 Boss gains 30% evasion — your attacks may miss!"
        elif "soul feast" in passive:
            self.boss_heals_on_hit = True
            text += "\n🩸 Boss now heals 30% of damage dealt each turn!"
        elif "heavy cleave" in passive:
            extra = int(self.boss['atk'] * 0.5)
            self.player_hp -= extra
            text += f"\n⚔️ Heavy Cleave deals an extra **{extra:,}** damage!"
        elif "bone armor" in passive:
            self.player_dmg_mult *= 0.75
            text += "\n🦴 Bone Armor activated — your damage reduced by 25%!"
        elif "screech" in passive:
            self.player_dmg_mult *= 0.80
            text += "\n😱 Screech — your damage reduced by 20%!"
        elif "blazing aura" in passive:
            self.boss_extra_fire = max(1, int(self.boss['atk'] * 0.15))
            text += f"\n🔥 Blazing Aura! Boss deals **{self.boss_extra_fire:,}** bonus fire damage each turn!"
        elif "terror" in passive:
            self.player_dmg_mult *= 0.85
            text += "\n😨 Terror — your damage reduced by 15%!"
        elif "mirage" in passive:
            self.player_evasion = 0.5
            text += "\n🌫️ Mirage! 50% of your attacks now hit a fake target!"
        elif "unstoppable" in passive:
            extra = int(self.boss['atk'] * 0.6)
            self.player_hp -= extra
            text += f"\n💥 Unstoppable surge — takes an extra swing for **{extra:,}** damage!"
        elif "permafrost" in passive:
            self.player_dmg_mult *= 0.75
            text += "\n❄️ Permafrost — your damage reduced by 25%!"
        elif "rebirth" in passive:
            self.boss_rebirth_ready = True
            text += "\n🔥 The Phoenix prepares to rise from the ashes!"
        elif "tidal shield" in passive:
            self.boss_shield = int(self.total_boss_hp * 0.10)
            text += f"\n🌊 Boss gains a **{self.boss_shield:,}** HP Tidal Shield!"
        elif "expose flaw" in passive:
            self.boss_atk_mult *= 1.5
            text += "\n🗡️ Expose Flaw — boss ATK increased by 50%!"
        elif "nullification" in passive:
            extra = int(self.boss['atk'] * 0.8)
            self.player_hp -= extra
            text += f"\n✨ Nullification strike deals **{extra:,}** damage!"
        elif "time loop" in passive:
            self.boss_attacks_twice = True
            text += "\n⏱️ Time Loop — boss now attacks twice each turn!"
        elif "cosmic collapse" in passive:
            extra = int(self.boss['atk'] * 2.0)
            self.player_hp -= extra
            text += f"\n💥 **Cosmic Collapse!** Catastrophic AoE deals **{extra:,}** damage!"
        elif "divine order" in passive:
            extra = int(self.boss['atk'] * 1.0)
            self.player_hp -= extra
            text += f"\n✨ Divine wrath descends — **{extra:,}** holy damage!"
        return text

    async def use_skill(self, interaction, skill_index):
        from main import RACE_SKILLS, get_skill_name
        race = self.player['race']
        level = self.player.get('level', 1)
        skill_name = get_skill_name(race, skill_index, level)

        best_atk = max(self.player['str'], self.player['mag'])
        raw_dmg = int(best_atk * 1.4 * self.player_dmg_mult)

        if random.random() < self.player_evasion:
            result = f"🌫️ Your **{skill_name}** hit a mirage — 0 damage!"
            dmg = 0
        else:
            if self.boss_shield > 0:
                tentative = calculate_damage(raw_dmg, self.boss['def'])
                absorbed = min(self.boss_shield, tentative)
                dmg = max(0, tentative - absorbed)
                self.boss_shield = max(0, self.boss_shield - absorbed)
                result = f"🌊 Shield absorbed **{absorbed:,}**! **{skill_name}** dealt **{dmg:,}** damage!"
            else:
                dmg = calculate_damage(raw_dmg, self.boss['def'])
                result = f"✨ **{skill_name}** dealt **{dmg:,}** damage!"
            self.boss_hp -= dmg
            self.total_damage += dmg
            if self.boss_extra_fire > 0:
                self.boss_hp -= self.boss_extra_fire
                result += f"\n🔥 Blazing Aura deals **{self.boss_extra_fire:,}** fire damage!"
        self.skill_uses += 1

        if not self.special_available and self.skill_uses >= 2:
            self.special_available = True
            special = RACE_SKILLS[race]['special']
            if level >= special['unlock_level']:
                self.children[4].disabled = False

        if not self.ability_used and self.boss_hp > 0 and self.boss_hp <= self.total_boss_hp * 0.5:
            self.ability_used = True
            result += self._apply_ability()

        if self.boss_hp <= 0:
            if self.boss_rebirth_ready and not self.boss_rebirth_used:
                self.boss_rebirth_used = True
                self.boss_rebirth_ready = False
                self.boss_hp = int(self.total_boss_hp * 0.3)
                result += f"\n🔥 **The Phoenix rises with {self.boss_hp:,} HP!**"
            else:
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(embed=await self.get_embed(result + "\n✅ **Boss defeated!**"), view=self)
                self.stop()
                return

        boss_atk = int(self.boss['atk'] * self.boss_atk_mult)
        boss_dmg = calculate_damage(boss_atk, self.player['def'])
        if self.boss_attacks_twice:
            boss_dmg += calculate_damage(boss_atk, self.player['def'])
        if self.boss_heals_on_hit and boss_dmg > 0:
            heal = int(boss_dmg * 0.3)
            self.boss_hp = min(self.total_boss_hp, self.boss_hp + heal)
            result += f"\n🩸 Boss healed **{heal:,}** HP!"
        self.player_hp -= boss_dmg
        result += f"\n{self.boss['name']} dealt **{boss_dmg:,}** back!"
        self.turn += 1

        if self.player_hp <= 0:
            self.player_hp = 0
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=await self.get_embed(result + "\n💀 **You were defeated!**"), view=self)
            self.stop()
            return

        await interaction.response.edit_message(embed=await self.get_embed(result), view=self)

    @discord.ui.button(label="Skill 1", style=discord.ButtonStyle.blurple, row=0)
    async def skill1(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_user(interaction):
            await interaction.response.send_message("This isn't your turn!", ephemeral=True)
            return
        await self.use_skill(interaction, 0)

    @discord.ui.button(label="Skill 2", style=discord.ButtonStyle.blurple, row=0)
    async def skill2(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_user(interaction):
            await interaction.response.send_message("This isn't your turn!", ephemeral=True)
            return
        await self.use_skill(interaction, 1)

    @discord.ui.button(label="Skill 3", style=discord.ButtonStyle.blurple, row=0)
    async def skill3(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_user(interaction):
            await interaction.response.send_message("This isn't your turn!", ephemeral=True)
            return
        await self.use_skill(interaction, 2)

    @discord.ui.button(label="Skill 4", style=discord.ButtonStyle.blurple, row=1)
    async def skill4(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_user(interaction):
            await interaction.response.send_message("This isn't your turn!", ephemeral=True)
            return
        await self.use_skill(interaction, 3)

    @discord.ui.button(label="Special", style=discord.ButtonStyle.green, row=1)
    async def special(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._check_user(interaction):
            await interaction.response.send_message("This isn't your turn!", ephemeral=True)
            return

        from main import RACE_SKILLS
        race = self.player['race']
        level = self.player.get('level', 1)
        special_data = RACE_SKILLS[race]['special']

        if level < special_data['unlock_level']:
            await interaction.response.send_message(f"Special unlocks at level {special_data['unlock_level']}!", ephemeral=True)
            return
        if not self.special_available:
            await interaction.response.send_message("Not ready! Use skills 2 more times.", ephemeral=True)
            return

        best_atk = max(self.player['str'], self.player['mag'])
        raw_sp = int(best_atk * 2.5 * self.player_dmg_mult)

        if random.random() < self.player_evasion:
            result = f"🌫️ Special **{special_data['name']}** hit a mirage — 0 damage!"
            dmg = 0
        else:
            if self.boss_shield > 0:
                tentative = calculate_damage(raw_sp, self.boss['def'] // 2)
                absorbed = min(self.boss_shield, tentative)
                dmg = max(0, tentative - absorbed)
                self.boss_shield = max(0, self.boss_shield - absorbed)
                result = f"🌊 Shield absorbed **{absorbed:,}**! **{special_data['name']}** dealt **{dmg:,}** MASSIVE damage!"
            else:
                dmg = calculate_damage(raw_sp, self.boss['def'] // 2)
                result = f"💫 **{special_data['name']}** dealt **{dmg:,}** MASSIVE damage!"
            self.boss_hp -= dmg
            self.total_damage += dmg
            if self.boss_extra_fire > 0:
                self.boss_hp -= self.boss_extra_fire
                result += f"\n🔥 Blazing Aura deals **{self.boss_extra_fire:,}** fire damage!"
        self.special_available = False
        self.skill_uses = 0
        self.children[4].disabled = True

        if not self.ability_used and self.boss_hp > 0 and self.boss_hp <= self.total_boss_hp * 0.5:
            self.ability_used = True
            result += self._apply_ability()

        if self.boss_hp <= 0:
            if self.boss_rebirth_ready and not self.boss_rebirth_used:
                self.boss_rebirth_used = True
                self.boss_rebirth_ready = False
                self.boss_hp = int(self.total_boss_hp * 0.3)
                result += f"\n🔥 **The Phoenix rises with {self.boss_hp:,} HP!**"
            else:
                for child in self.children:
                    child.disabled = True
                await interaction.response.edit_message(embed=await self.get_embed(result + "\n✅ **Boss defeated!**"), view=self)
                self.stop()
                return

        boss_atk = int(self.boss['atk'] * self.boss_atk_mult)
        boss_dmg = calculate_damage(boss_atk, self.player['def'])
        if self.boss_attacks_twice:
            boss_dmg += calculate_damage(boss_atk, self.player['def'])
        if self.boss_heals_on_hit and boss_dmg > 0:
            heal = int(boss_dmg * 0.3)
            self.boss_hp = min(self.total_boss_hp, self.boss_hp + heal)
            result += f"\n🩸 Boss healed **{heal:,}** HP!"
        self.player_hp -= boss_dmg
        result += f"\n{self.boss['name']} dealt **{boss_dmg:,}** back!"
        self.turn += 1

        if self.player_hp <= 0:
            self.player_hp = 0
            for child in self.children:
                child.disabled = True
            await interaction.response.edit_message(embed=await self.get_embed(result + "\n💀 **You were defeated!**"), view=self)
            self.stop()
            return

        await interaction.response.edit_message(embed=await self.get_embed(result), view=self)

class Raid(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.loop.create_task(self.auto_spawn_raids())

    async def auto_spawn_raids(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            await asyncio.sleep(random.randint(3600, 7200))
            for guild in self.bot.guilds:
                active_channel = None
                most_recent = 0
                for channel in guild.text_channels:
                    try:
                        messages = [m async for m in channel.history(limit=10)]
                        if messages:
                            latest = messages[0].created_at.timestamp()
                            if latest > most_recent:
                                most_recent = latest
                                active_channel = channel
                    except:
                        continue

                if active_channel:
                    boss = random.choice(BOSSES)
                    await self.spawn_raid(active_channel, boss, None)

    async def spawn_raid(self, channel, boss, spawner_id, spawner_name=None):
        view = RaidJoinView(boss, spawner_id, channel)

        if spawner_id and spawner_name:
            p = players.search(Player.id == spawner_id)
            if p:
                p = p[0]
                view.players.append({
                    'id': spawner_id,
                    'name': spawner_name,
                    'hp': p['hp'],
                    'str': p['str'],
                    'mag': p['mag'],
                    'def': p['def'],
                    'level': p.get('level', 1),
                    'race': p['race']
                })

        embed = discord.Embed(
            title=f"👹 RAID SPAWNED — {boss['name']}!",
            description=f"**Passive:** {boss['passive']} — *{boss['passive_desc']}*\n\nClick **Enter Raid** to join! Max 5 players.",
            color=0xFF4444)
        embed.add_field(name="❤️ HP", value=f"`{boss['hp']:,}`", inline=True)
        embed.add_field(name="⚔️ ATK", value=f"`{boss['atk']:,}`", inline=True)
        embed.add_field(name="🛡️ DEF", value=f"`{boss['def']:,}`", inline=True)
        embed.add_field(name="🏆 Tier", value=f"`{TIER_NAMES[boss['tier']]}`", inline=True)
        embed.add_field(name="⏰ Join Timer", value="`5 minutes`", inline=True)
        embed.add_field(name="👥 Max Players", value="`5`", inline=True)
        embed.set_footer(text="Nexworld RPG • A powerful enemy has appeared!")

        msg = await channel.send(embed=embed, view=view)
        view.message = msg

        await asyncio.sleep(300)

        if not view.started:
            if len(view.players) == 0:
                for child in view.children:
                    child.disabled = True
                await msg.edit(
                    embed=discord.Embed(
                        title="❌ Raid Expired",
                        description="No players joined the raid in time!",
                        color=0xFF0000),
                    view=view)
                return

            view.started = True
            for child in view.children:
                child.disabled = True
            await msg.edit(view=view)
            await view.start_raid()

    @commands.command()
    async def raid(self, ctx, action: str = None):
        user_id = str(ctx.author.id)
        p = players.search(Player.id == user_id)

        if not p:
            await ctx.send(embed=discord.Embed(
                description="❌ You haven't started yet! Use `!start` to begin.",
                color=GOLD))
            return

        p = p[0]

        if action == "spawn" or action is None:
            inv = p.get('inventory', [])
            raid_pass = next((i for i in inv if i['name'] == 'Raid Pass'), None)

            if not raid_pass:
                await ctx.send(embed=discord.Embed(
                    title="❌ No Raid Pass!",
                    description="You need a **Raid Pass** to spawn a raid!\nBuy one from `!shop 1` for `15,000` Nexcoins.",
                    color=GOLD))
                return

            class ConfirmRaidView(discord.ui.View):
                def __init__(self_inner):
                    super().__init__(timeout=30)

                @discord.ui.button(label="✅ Yes", style=discord.ButtonStyle.green)
                async def confirm(self_inner, interaction: discord.Interaction, button: discord.ui.Button):
                    if interaction.user.id != ctx.author.id:
                        await interaction.response.send_message("This isn't your raid!", ephemeral=True)
                        return

                    new_inv = [i for i in inv if i['uid'] != raid_pass['uid']]
                    players.update({'inventory': new_inv}, Player.id == user_id)

                    boss = random.choice(BOSSES)
                    await interaction.response.edit_message(
                        embed=discord.Embed(
                            description=f"🎲 Summoning **{boss['name']}**!",
                            color=GOLD),
                        view=None)
                    await self.spawn_raid(ctx.channel, boss, user_id, ctx.author.name)

                @discord.ui.button(label="❌ No", style=discord.ButtonStyle.red)
                async def cancel(self_inner, interaction: discord.Interaction, button: discord.ui.Button):
                    await interaction.response.edit_message(
                        embed=discord.Embed(description="Raid cancelled.", color=GOLD),
                        view=None)

            embed = discord.Embed(
                title="⚔️ Summon a Raid?",
                description="1x Raid Pass will be used.\nA random boss will spawn in this channel!\nOther players can join for 5 minutes.",
                color=GOLD)
            await ctx.send(embed=embed, view=ConfirmRaidView())

async def setup(bot):
    await bot.add_cog(Raid(bot))