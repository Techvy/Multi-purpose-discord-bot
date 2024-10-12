import json
import logging
import os
import platform
import sys
import discord
from discord.ext import commands, tasks
from discord.ext.commands import Context
os.system("cls")
cfgpth = f"{os.path.realpath(os.path.dirname(__file__))}/config.json"
if not os.path.isfile(cfgpth):
    sys.exit("'config.json' not found! Please add it and try again.")
else:
    with open(cfgpth) as f:
        cfg = json.load(f)

intents = discord.Intents.all()

class LogFormatter(logging.Formatter):
    blk = "\x1b[30m"
    red = "\x1b[31m"
    grn = "\x1b[32m"
    ylw = "\x1b[33m"
    blu = "\x1b[34m"
    gry = "\x1b[38m"
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLS = {
        logging.DEBUG: gry + bold,
        logging.INFO: blu + bold,
        logging.WARNING: ylw + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLS[record.levelno]
        fmt = "(blk){asctime}(reset) (lvlcolor){levelname:<8}(reset) (grn){name}(reset) {message}"
        fmt = fmt.replace("(blk)", self.blk + self.bold)
        fmt = fmt.replace("(reset)", self.reset)
        fmt = fmt.replace("(lvlcolor)", log_color)
        fmt = fmt.replace("(grn)", self.grn + self.bold)
        formatter = logging.Formatter(fmt, "%Y-%m-%d %H:%M:%S", style="{")
        return formatter.format(record)

logger = logging.getLogger("discord_bot")
logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler()
console_handler.setFormatter(LogFormatter())
file_handler = logging.FileHandler(filename="discord.log", encoding="utf-8", mode="w")
file_handler_formatter = logging.Formatter(
    "[{asctime}] [{levelname:<8}] {name}: {message}", "%Y-%m-%d %H:%M:%S", style="{"
)
file_handler.setFormatter(file_handler_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)

class DiscordBot(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(cfg["prefix"]),
            intents=intents,
            help_command=None,
        )
        self.logger = logger
        self.cfg = cfg
        self.db = None

    async def setup_db(self) -> None:
        import sqlite3
        self.db = sqlite3.connect('your_database_file.db')
        c = self.db.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS claim (
                        role_id INTEGER, 
                        guild INTEGER, 
                        claim_time INTEGER
                    )''')
        c.execute('''CREATE TABLE IF NOT EXISTS gw (
                        c_id INTEGER, 
                        m_id INTEGER, 
                        end REAL, 
                        winners INTEGER, 
                        prize TEXT, 
                        host INTEGER, 
                        ended BOOLEAN
                    )''')
        self.db.commit()
        c.close()

    async def load_cogs(self) -> None:
        base_dir = os.path.realpath(os.path.dirname(__file__)) + '/cogs'
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith(".py") and file != '__init__.py':
                    rel_path = os.path.relpath(os.path.join(root, file), base_dir)
                    mod_path = os.path.splitext(rel_path)[0].replace(os.sep, '.')
                    if file == '__init__.py':
                        continue
                    try:
                        await self.load_extension(f"cogs.{mod_path}")
                    except Exception as e:
                        exc = f"{type(e).__name__}: {e}"
                        self.logger.error(
                            f"Failed to load extension {mod_path}\n{exc}"
                        )

    @tasks.loop( )
    async def status_task(self) -> None:
        await self.change_presence(activity=discord.Game(name="/help | Techvy"))

    @status_task.before_loop
    async def before_status_task(self) -> None:
        await self.wait_until_ready()

    async def setup_hook(self) -> None:
        await self.setup_db()
        self.logger.info(f"Logged in as {self.user.name}")
        await self.load_cogs()
        self.status_task.start()

    async def on_message(self, message: discord.Message) -> None:
        if message.author == self.user or message.author.bot:
            return
        await self.process_commands(message)

    async def on_command_completion(self, ctx: Context) -> None:
        cmd = ctx.command.qualified_name.split(" ")[0]
        if ctx.guild:
            self.logger.info(
                f"Executed {cmd} command in {ctx.guild.name} (ID: {ctx.guild.id}) by {ctx.author} (ID: {ctx.author.id})"
            )
        else:
            self.logger.info(
                f"Executed {cmd} command by {ctx.author} (ID: {ctx.author.id}) in DMs"
            )

    async def on_command_error(self, ctx: Context, err) -> None:
        if isinstance(err, commands.CommandOnCooldown):
            min, sec = divmod(err.retry_after, 60)
            hrs, min = divmod(min, 60)
            hrs = hrs % 24
            embed = discord.Embed(
                description=f"**Please slow down** - You can use this command again in {f'{round(hrs)} hours' if round(hrs) > 0 else ''} {f'{round(min)} minutes' if round(min) > 0 else ''} {f'{round(sec)} seconds' if round(sec) > 0 else ''}.",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(err, commands.NotOwner):
            embed = discord.Embed(
                description="You are not the owner of the bot!", color=0xE02B2B
            )
            await ctx.send(embed=embed)
            if ctx.guild:
                self.logger.warning(
                    f"{ctx.author} (ID: {ctx.author.id}) tried to execute an owner only command in the guild {ctx.guild.name} (ID: {ctx.guild.id}), but the user is not an owner of the bot."
                )
            else:
                self.logger.warning(
                    f"{ctx.author} (ID: {ctx.author.id}) tried to execute an owner only command in the bot's DMs, but the user is not an owner of the bot."
                )
        elif isinstance(err, commands.MissingPermissions):
            embed = discord.Embed(
                description="You are missing the permission(s) "
                + ", ".join(err.missing_permissions)
                + " to execute this command!",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(err, commands.BotMissingPermissions):
            embed = discord.Embed(
                description="I am missing the permission(s) "
                + ", ".join(err.missing_permissions)
                + " to fully perform this command!",
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        elif isinstance(err, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="Error!",
                description=str(err).capitalize(),
                color=0xE02B2B,
            )
            await ctx.send(embed=embed)
        else:
            raise err

bot = DiscordBot()
bot.run(cfg["token"])
