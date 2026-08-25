import shlex
import time

import discord
from discord.ext import commands
from tinydb import Query

from db import mail_table, players, Player, generate_item_uid, generate_mail_id
from main import ADMIN_IDS, GOLD, NC_ICON, SS_ICON


MailQ = Query()


def _is_admin(user_id):
    return str(user_id) in ADMIN_IDS


def _parse_admin_payload(payload):
    """Parse: "Subject" "Message" [--reward type:value ...]."""
    try:
        parts = shlex.split(payload or "")
    except ValueError:
        return None, None, [], "Use double quotes around the subject and message."

    rewards = []
    clean = []
    index = 0
    while index < len(parts):
        if parts[index].lower() == "--reward":
            if index + 1 >= len(parts):
                return None, None, [], "Each `--reward` needs a value."
            rewards.append(parts[index + 1])
            index += 2
        else:
            clean.append(parts[index])
            index += 1

    if len(clean) < 2:
        return None, None, [], 'Format: `"Subject" "Message"`'
    subject = clean[0].strip()
    message = " ".join(clean[1:]).strip()
    if not subject or not message:
        return None, None, [], "Subject and message cannot be empty."

    parsed_rewards = []
    for reward in rewards:
        parsed, error = _parse_reward(reward)
        if error:
            return None, None, [], error
        parsed_rewards.append(parsed)
    return subject, message, parsed_rewards, None


def _parse_reward(value):
    """Parse starshard:500, nexcoin:1000, or item:Rare:Dragon Blade."""
    pieces = value.split(":", 2)
    kind = pieces[0].lower().strip()
    if kind in ("nexcoin", "nexcoins", "starshard", "starshards"):
        if len(pieces) != 2:
            return None, f"Invalid currency reward `{value}`. Use `nexcoin:1000` or `starshard:5`."
        try:
            amount = int(pieces[1])
        except ValueError:
            return None, f"Invalid reward amount in `{value}`."
        if amount <= 0:
            return None, "Reward amounts must be greater than zero."
        return {"type": "nexcoins" if kind.startswith("nexcoin") else "starshards", "amount": amount}, None

    if kind == "item":
        if len(pieces) == 2:
            rarity, name = "Common", pieces[1].strip()
        elif len(pieces) == 3:
            rarity, name = pieces[1].strip(), pieces[2].strip()
        else:
            return None, f"Invalid item reward `{value}`. Use `item:Rare:Item Name`."
        if not name:
            return None, "Item rewards need an item name."
        return {"type": "item", "name": name, "rarity": rarity or "Common"}, None

    return None, f"Unknown reward type `{pieces[0]}`. Use `nexcoin`, `starshard`, or `item`."


def _reward_summary(rewards):
    if not rewards:
        return "No attached rewards"
    summary = []
    for reward in rewards:
        if reward["type"] == "nexcoins":
            summary.append(f"{NC_ICON} {reward['amount']:,} Nexcoins")
        elif reward["type"] == "starshards":
            summary.append(f"{SS_ICON} {reward['amount']:,} Starshards")
        else:
            summary.append(f"1x {reward['name']} ({reward['rarity']})")
    return "\n".join(summary)


def _mail_embed(mail, full=False):
    unread = "🔴" if not mail.get("read", False) else "⚪"
    embed = discord.Embed(
        title=f"📬 {mail['subject']}",
        description=mail["message"] if full else f"From: **{mail.get('sender_name', 'Nexworld Administration')}**",
        color=GOLD,
    )
    embed.add_field(name="Mail ID", value=f"`#{mail['id']}`", inline=True)
    embed.add_field(name="Status", value=f"{unread} {'Unread' if not mail.get('read', False) else 'Read'}", inline=True)
    if full:
        embed.add_field(name="From", value=mail.get("sender_name", "Nexworld Administration"), inline=False)
        embed.add_field(name="Attached Rewards", value=_reward_summary(mail.get("rewards", [])), inline=False)
        if mail.get("rewards") and mail.get("claimed"):
            embed.set_footer(text="Rewards claimed • Nexworld RPG")
        elif mail.get("rewards"):
            embed.set_footer(text=f"Use !mail claim {mail['id']} to collect rewards")
    else:
        embed.add_field(name="Preview", value=mail["message"][:900], inline=False)
    return embed


class Mail(commands.Cog, name="Mail"):
    def __init__(self, bot):
        self.bot = bot

    async def _notify(self, recipient_id, mail):
        try:
            user = self.bot.get_user(int(recipient_id))
            if user is None:
                user = await self.bot.fetch_user(int(recipient_id))
            await user.send(
                embed=discord.Embed(
                    title="📬 You have received a new mail!",
                    description=f"**{mail['subject']}**\nUse `!mail {mail['id']}` to read it.",
                    color=GOLD,
                )
            )
        except Exception:
            # A closed or disabled DM must not prevent mail delivery to the inbox.
            pass

    async def _create_mail(self, recipient_id, subject, message, rewards, sender_id, sender_name):
        mail = {
            "id": generate_mail_id(),
            "recipient_id": str(recipient_id),
            "sender_id": str(sender_id),
            "sender_name": sender_name,
            "subject": subject,
            "message": message,
            "rewards": rewards,
            "read": False,
            "claimed": False,
            "created_at": time.time(),
        }
        mail_table.insert(mail)
        await self._notify(recipient_id, mail)
        return mail

    async def _require_admin(self, ctx):
        if _is_admin(ctx.author.id):
            return True
        await ctx.send(embed=discord.Embed(description="❌ No permission.", color=GOLD))
        return False

    @commands.command(name="mail", aliases=["inbox"])
    async def mail(self, ctx, action=None, *, extra=None):
        user_id = str(ctx.author.id)
        if action is None:
            action = "list"
        action = str(action).lower()

        if action == "help":
            await ctx.send(embed=discord.Embed(
                title="📬 NexMail Commands",
                description=(
                    "`!mail` — Open your mailbox\n"
                    "`!mail <ID>` — Read a mail\n"
                    "`!mail claim <ID>` — Claim attached rewards\n"
                    "`!mail delete <ID>` — Delete a mail\n"
                    "`!mail readall` — Mark all mails as read\n"
                    "`!mail deleteall` — Delete all read mails\n"
                    "`!mail sent` — View your sent system mail (admin only)\n"
                    "`!mail help` — Show this help\n"
                    "`!inbox` — Alias for `!mail`"
                ),
                color=GOLD,
            ))
            return

        if action == "sent":
            if not await self._require_admin(ctx):
                return
            sent = sorted(mail_table.search(MailQ.sender_id == user_id), key=lambda item: item["id"], reverse=True)[:10]
            if not sent:
                await ctx.send(embed=discord.Embed(title="📤 Sent Mail", description="No sent mail yet.", color=GOLD))
                return
            lines = [f"`#{item['id']}` **{item['subject']}** → <@{item['recipient_id']}>" for item in sent]
            await ctx.send(embed=discord.Embed(title="📤 Sent System Mail", description="\n".join(lines), color=GOLD))
            return

        if action in ("readall", "deleteall"):
            user_mail = mail_table.search(MailQ.recipient_id == user_id)
            if action == "readall":
                for item in user_mail:
                    if not item.get("read", False):
                        mail_table.update({"read": True}, MailQ.id == item["id"])
                await ctx.send(embed=discord.Embed(description="✅ All mail marked as read.", color=GOLD))
            else:
                deleted = 0
                for item in user_mail:
                    if item.get("read", False):
                        mail_table.remove(MailQ.id == item["id"])
                        deleted += 1
                await ctx.send(embed=discord.Embed(description=f"✅ Deleted {deleted} read mail(s).", color=GOLD))
            return

        if action in ("claim", "delete"):
            if not extra:
                await ctx.send(embed=discord.Embed(description=f"Usage: `!mail {action} <ID>`", color=GOLD))
                return
            mail_id = extra.strip().split()[0].lstrip("#")
        elif action.isdigit():
            mail_id = action
        elif action == "list":
            mail_id = None
        else:
            await ctx.send(embed=discord.Embed(description="Unknown mail command. Use `!mail help`.", color=GOLD))
            return

        if mail_id is not None:
            try:
                mail_id = int(mail_id)
            except ValueError:
                await ctx.send(embed=discord.Embed(description="❌ Mail ID must be a number.", color=GOLD))
                return
            result = mail_table.search((MailQ.id == mail_id) & (MailQ.recipient_id == user_id))
            if not result:
                await ctx.send(embed=discord.Embed(description=f"❌ Mail `#{mail_id}` not found.", color=GOLD))
                return
            item = result[0]
            if action == "claim":
                if item.get("claimed", False):
                    await ctx.send(embed=discord.Embed(description="❌ The rewards from this mail were already claimed.", color=GOLD))
                    return
                rewards = item.get("rewards", [])
                player = players.search(Player.id == user_id)
                if not player:
                    await ctx.send(embed=discord.Embed(description="❌ You haven't started yet! Use `!start`.", color=GOLD))
                    return
                player = player[0]
                inventory = player.get("inventory", [])
                updates = {}
                claimed_lines = []
                for reward in rewards:
                    if reward["type"] == "nexcoins":
                        updates["nexcoins"] = player.get("nexcoins", 0) + reward["amount"]
                        player["nexcoins"] = updates["nexcoins"]
                        claimed_lines.append(f"{NC_ICON} `{reward['amount']:,}` Nexcoins")
                    elif reward["type"] == "starshards":
                        updates["starshards"] = player.get("starshards", 0) + reward["amount"]
                        player["starshards"] = updates["starshards"]
                        claimed_lines.append(f"{SS_ICON} `{reward['amount']:,}` Starshards")
                    elif reward["type"] == "item":
                        uid = generate_item_uid()
                        inventory.append({
                            "uid": uid,
                            "name": reward["name"],
                            "rarity": reward["rarity"],
                            "type": "mail_reward",
                            "stats": {},
                        })
                        claimed_lines.append(f"`({uid})` {reward['name']} ({reward['rarity']})")
                updates["inventory"] = inventory
                players.update(updates, Player.id == user_id)
                mail_table.update({"claimed": True, "read": True}, MailQ.id == mail_id)
                await ctx.send(embed=discord.Embed(
                    title="🎁 Mail Rewards Claimed!",
                    description="\n".join(claimed_lines) if claimed_lines else "This mail has no attached rewards.",
                    color=GOLD,
                ))
                return
            if action == "delete":
                mail_table.remove(MailQ.id == mail_id)
                await ctx.send(embed=discord.Embed(description=f"✅ Mail `#{mail_id}` deleted.", color=GOLD))
                return

            mail_table.update({"read": True}, MailQ.id == mail_id)
            item["read"] = True
            await ctx.send(embed=_mail_embed(item, full=True))
            return

        inbox = sorted(mail_table.search(MailQ.recipient_id == user_id), key=lambda item: item["id"], reverse=True)
        if not inbox:
            await ctx.send(embed=discord.Embed(title="📬 NexMail", description="Your mailbox is empty.", color=GOLD))
            return
        unread = sum(1 for item in inbox if not item.get("read", False))
        lines = [
            f"{'🔴' if not item.get('read', False) else '⚪'} `#{item['id']}` **{item['subject']}**"
            for item in inbox[:15]
        ]
        description = f"**{unread} unread message(s)**\n\n" + "\n".join(lines)
        description += "\n\nUse `!mail <ID>` to read a message."
        await ctx.send(embed=discord.Embed(title="📬 NEXMAIL", description=description, color=GOLD))

    @commands.command(name="sendmail")
    async def sendmail(self, ctx, member: discord.Member = None, *, payload=None):
        if not await self._require_admin(ctx):
            return
        if member is None or not payload:
            await ctx.send(embed=discord.Embed(
                description='Usage: `!sendmail @user "Subject" "Message" [--reward type:value]`',
                color=GOLD,
            ))
            return
        subject, message, rewards, error = _parse_admin_payload(payload)
        if error:
            await ctx.send(embed=discord.Embed(description=f"❌ {error}", color=GOLD))
            return
        mail = await self._create_mail(member.id, subject, message, rewards, ctx.author.id, "Nexworld Administration")
        await ctx.send(embed=discord.Embed(
            title="✅ Mail Sent",
            description=f"Sent `#{mail['id']}` to {member.mention}.\n\nAttached rewards:\n{_reward_summary(rewards)}",
            color=GOLD,
        ))

    @commands.command(name="sendmailall")
    async def sendmailall(self, ctx, *, payload=None):
        if not await self._require_admin(ctx):
            return
        if not payload:
            await ctx.send(embed=discord.Embed(
                description='Usage: `!sendmailall "Subject" "Message" [--reward type:value]`',
                color=GOLD,
            ))
            return
        subject, message, rewards, error = _parse_admin_payload(payload)
        if error:
            await ctx.send(embed=discord.Embed(description=f"❌ {error}", color=GOLD))
            return
        recipients = players.all()
        if not recipients:
            await ctx.send(embed=discord.Embed(description="❌ There are no registered players.", color=GOLD))
            return
        sent = 0
        for player in recipients:
            await self._create_mail(
                player["id"], subject, message, rewards, ctx.author.id, "Nexworld Administration"
            )
            sent += 1
        await ctx.send(embed=discord.Embed(
            title="✅ Mail Sent to All Players",
            description=f"Delivered {sent} mail(s).\n\nAttached rewards:\n{_reward_summary(rewards)}",
            color=GOLD,
        ))

    @commands.command(name="mailreward")
    async def mailreward(self, ctx, member: discord.Member = None, mail_id: int = None, *, reward=None):
        if not await self._require_admin(ctx):
            return
        if member is None or mail_id is None or not reward:
            await ctx.send(embed=discord.Embed(
                description="Usage: `!mailreward @user <mail ID> <type:value>`",
                color=GOLD,
            ))
            return
        parsed, error = _parse_reward(reward.strip())
        if error:
            await ctx.send(embed=discord.Embed(description=f"❌ {error}", color=GOLD))
            return
        result = mail_table.search((MailQ.id == mail_id) & (MailQ.recipient_id == str(member.id)))
        if not result:
            await ctx.send(embed=discord.Embed(description=f"❌ Mail `#{mail_id}` not found for that player.", color=GOLD))
            return
        item = result[0]
        if item.get("claimed", False):
            await ctx.send(embed=discord.Embed(description="❌ This mail has already been claimed.", color=GOLD))
            return
        rewards = item.get("rewards", [])
        rewards.append(parsed)
        mail_table.update({"rewards": rewards}, MailQ.id == mail_id)
        await ctx.send(embed=discord.Embed(
            title="✅ Mail Reward Attached",
            description=f"Added `{reward}` to mail `#{mail_id}` for {member.mention}.",
            color=GOLD,
        ))

    @commands.command(name="announce")
    async def announce(self, ctx, *, payload=None):
        if not await self._require_admin(ctx):
            return
        if not payload:
            await ctx.send(embed=discord.Embed(
                description='Usage: `!announce "Subject" "Message" [--reward type:value]`',
                color=GOLD,
            ))
            return
        subject, message, rewards, error = _parse_admin_payload(payload)
        if error:
            await ctx.send(embed=discord.Embed(description=f"❌ {error}", color=GOLD))
            return
        recipients = players.all()
        for player in recipients:
            await self._create_mail(
                player["id"], subject, message, rewards, ctx.author.id, "Nexworld Administration"
            )
        await ctx.send(embed=discord.Embed(
            title="✅ Announcement Sent",
            description=f"Created mail for {len(recipients)} player(s).",
            color=GOLD,
        ))


async def setup(bot):
    await bot.add_cog(Mail(bot))