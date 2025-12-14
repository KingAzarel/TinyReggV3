# cogs/admin.py

import logging
from discord.ext import commands
from utils import BOT_OWNER_ID

logger = logging.getLogger("tinyregg.admin")


# ─────────────────────────────────────────────────────────────
# Owner-only gate
# ─────────────────────────────────────────────────────────────
def owner_only():
    async def predicate(ctx: commands.Context):
        return ctx.author.id == BOT_OWNER_ID
    return commands.check(predicate)


class AdminCog(commands.Cog):
    """
    Owner-only administrative controls for TinyRegg.
    """

    def __init__(self, bot):
        self.bot = bot

    # ─────────────────────────────────────────────────────────────
    # Utility: safe-call helper
    # Prevents crashes if a method is not wired yet
    # ─────────────────────────────────────────────────────────────
    async def _safe_call(self, fn_name: str, *args):
        fn = getattr(self.bot, fn_name, None)
        if not fn:
            logger.error("ADMIN attempted missing fn: %s", fn_name)
            return False

        await fn(*args)
        return True

    # ─────────────────────────────────────────────────────────────
    # RESEND DAILY TASKS
    # ─────────────────────────────────────────────────────────────
    @commands.command(name="resend_tasks")
    @owner_only()
    async def resend_tasks(self, ctx):
        ok = await self._safe_call("dispatch_daily_tasks")
        if ok:
            await ctx.send("🔁 Daily tasks resent.")
            logger.warning("ADMIN resend_tasks by %s", ctx.author.id)

    # ─────────────────────────────────────────────────────────────
    # FORCE DAILY RESET (global)
    # ─────────────────────────────────────────────────────────────
    @commands.command(name="reset_day")
    @owner_only()
    async def reset_day(self, ctx):
        ok = await self._safe_call("force_daily_reset")
        if ok:
            await ctx.send("🕛 Daily state reset.")
            logger.warning("ADMIN reset_day by %s", ctx.author.id)

    # ─────────────────────────────────────────────────────────────
    # RESET SINGLE USER
    # ─────────────────────────────────────────────────────────────
    @commands.command(name="reset_user")
    @owner_only()
    async def reset_user(self, ctx, user_id: int):
        ok = await self._safe_call("reset_user_state", user_id)
        if ok:
            await ctx.send(f"♻️ User `{user_id}` reset.")
            logger.warning(
                "ADMIN reset_user user=%s by=%s",
                user_id,
                ctx.author.id,
            )

    # ─────────────────────────────────────────────────────────────
    # SET STREAK
    # ─────────────────────────────────────────────────────────────
    @commands.command(name="set_streak")
    @owner_only()
    async def set_streak(self, ctx, user_id: int, value: int):
        if value < 0:
            await ctx.send("❌ Streak cannot be negative.")
            return

        ok = await self._safe_call("set_user_streak", user_id, value)
        if ok:
            await ctx.send(f"🔥 Streak for `{user_id}` set to `{value}`.")
            logger.critical(
                "ADMIN set_streak user=%s value=%s by=%s",
                user_id,
                value,
                ctx.author.id,
            )

    # ─────────────────────────────────────────────────────────────
    # TOKEN ECONOMY
    # ─────────────────────────────────────────────────────────────
    @commands.command(name="add_tokens")
    @owner_only()
    async def add_tokens(self, ctx, user_id: int, amount: int):
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.")
            return

        ok = await self._safe_call("add_tokens", user_id, amount)
        if ok:
            await ctx.send(f"🪙 Added `{amount}` tokens to `{user_id}`.")
            logger.warning(
                "ADMIN add_tokens user=%s amount=%s by=%s",
                user_id,
                amount,
                ctx.author.id,
            )

    @commands.command(name="remove_tokens")
    @owner_only()
    async def remove_tokens(self, ctx, user_id: int, amount: int):
        if amount <= 0:
            await ctx.send("❌ Amount must be positive.")
            return

        ok = await self._safe_call("remove_tokens", user_id, amount)
        if ok:
            await ctx.send(f"🪙 Removed `{amount}` tokens from `{user_id}`.")
            logger.warning(
                "ADMIN remove_tokens user=%s amount=%s by=%s",
                user_id,
                amount,
                ctx.author.id,
            )

    # ─────────────────────────────────────────────────────────────
    # RESYNC SLASH COMMANDS
    # ─────────────────────────────────────────────────────────────
    @commands.command(name="resync")
    @owner_only()
    async def resync(self, ctx):
        synced = await self.bot.tree.sync()
        await ctx.send(f"🔄 Resynced `{len(synced)}` commands.")
        logger.warning("ADMIN resync by %s", ctx.author.id)

    # ─────────────────────────────────────────────────────────────
    # SOFT SHUTDOWN (Railway will restart)
    # ─────────────────────────────────────────────────────────────
    @commands.command(name="shutdown")
    @owner_only()
    async def shutdown(self, ctx):
        await ctx.send("🛑 Shutting down.")
        logger.critical("ADMIN shutdown by %s", ctx.author.id)
        await self.bot.close()


# ─────────────────────────────────────────────────────────────
# Cog setup
# ─────────────────────────────────────────────────────────────
async def setup(bot):
    await bot.add_cog(AdminCog(bot))
