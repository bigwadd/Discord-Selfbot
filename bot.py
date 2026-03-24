import discord
import asyncio
import re
import aiohttp
import json
import os
import platform
import psutil
import requests
import random
import io
from PIL import Image
from discord.ext import commands
from concurrent.futures import ThreadPoolExecutor


TOKEN = 'add your acc token here'
PREFIX = '.'

bot = commands.Bot(command_prefix=PREFIX, self_bot=True, heartbeat_timeout=60, guild_subscriptions=False)

active_reaction = {'emoji': None, 'enabled': False}
auto_responses = {}
auto_messages = {}
auto_message_tasks = {}
status_rotation_task = None
status_rotation_active = False
status_rotation_data = {}
rpc_client = None
rpc_active = False
afk_data = {}
afk_cooldowns = {}

executor = ThreadPoolExecutor(max_workers=10)

supported_currencies = {
    'btc': 'bitcoin', 
    'eth': 'ethereum', 
    'ltc': 'litecoin', 
    'xrp': 'ripple', 
    'usdt': 'tether', 
    'usdc': 'usd-coin',
    'doge': 'dogecoin',
}

terry_quotes = [
    "Terrence Andrew Davis (December 15, 1969 – August 11, 2018) was an American electrical engineer, computer programmer, and outsider artist best known for creating and designing TempleOS.",
    "Davis became an atheist and described himself as a scientific materialist until experiencing what he called a 'revelation from God'.",
    "Starting in 1996, Davis was admitted to a psychiatric ward around every six months for reoccurring manic episodes.",
    "He donated large sums of money to charity organizations, something he had never done before. Later, he surmised, 'that act probably caused God to reveal Himself to me and saved me.'",
    "Davis was initially diagnosed with bipolar disorder and later declared to have schizophrenia.",
    "He felt 'guilty for being such a technology-advocate atheist' and tried to follow Jesus by giving away all of his possessions and living a nomadic lifestyle.",
    "TempleOS is a biblical-themed operating system designed to be the Third Temple prophesized in the Bible.",
    "Davis proclaimed that he was in direct communication with God, who told him to build a successor to the Second Temple as an operating system.",
    "The system's 640×480 resolution and 16-color display were explicit instructions from God.",
    "Davis used the oracle to ask God about war ('servicemen competing'), death ('awful'), dinosaurs ('Brontosaurs' feet hurt when stepped'), favorite video game (Donkey Kong), favorite car (BMW), favorite national anthem (Latvia's), favorite band (the Beatles).",
    "Eight months before his death, he struggled with periods of homelessness. His fans brought him supplies, but Davis refused their offers of housing.",
    "In August 2018, he was struck by a train and died at the age of 48."
]

B = '\u001b[34m'
LB = '\u001b[36m'
W = '\u001b[0m'
BB = '\u001b[1;34m'
LG = '\u001b[92m'
LR = '\u001b[91m'

def bluetxt(txt):
    out = ''
    for c in txt:
        if c.isalpha():
            out += f'{B}{c}{W}'
        else:
            out += c
    return out

def load_afk_data():
    global afk_data
    try:
        with open("afk_data.json", "r") as f:
            afk_data = json.load(f)
    except FileNotFoundError:
        afk_data = {}

def save_afk_data():
    with open("afk_data.json", "w") as f:
        json.dump(afk_data, f)

def load_auto_responses():
    global auto_responses
    try:
        with open("auto_responses.json", "r") as file:
            auto_responses = json.load(file)
    except FileNotFoundError:
        auto_responses = {}

def save_auto_responses():
    with open("auto_responses.json", "w") as file:
        json.dump(auto_responses, file, indent=4)

def load_auto_messages():
    global auto_messages
    try:
        with open("auto_messages.json", "r") as file:
            auto_messages = json.load(file)
    except FileNotFoundError:
        auto_messages = {}

def save_auto_messages():
    with open("auto_messages.json", "w") as file:
        json.dump(auto_messages, file, indent=4)

def load_status_rotation():
    global status_rotation_data
    try:
        with open("status_rotation.json", "r") as f:
            status_rotation_data = json.load(f)
    except FileNotFoundError:
        status_rotation_data = {"statuses": [], "current_mode": "online", "enabled": False}

def save_status_rotation():
    with open("status_rotation.json", "w") as f:
        json.dump(status_rotation_data, f, indent=4)

def detect_crypto(addr):
    addr = addr.strip()
    if addr.startswith('0x') and len(addr) == 42:
        return 'eth'
    elif addr.startswith(('1', '3', 'bc1')) and 26 <= len(addr) <= 42:
        return 'btc'
    elif addr.startswith('L') and len(addr) in [34, 43]:
        return 'ltc'
    elif addr.startswith('D') and len(addr) in [34, 43]:
        return 'doge'
    elif len(addr) in [34, 43]:
        return 'ltc'
    return None

async def get_crypto_price(crypto_id):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://api.coingecko.com/api/v3/simple/price?ids={crypto_id}&vs_currencies=usd', timeout=5) as r:
                if r.status == 200:
                    data = await r.json()
                    return data[crypto_id]['usd']
    except:
        pass
    return None

async def get_btc_balance(address):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance', timeout=8) as r:
                if r.status == 200:
                    d = await r.json()
                    bal = d['balance'] / 10**8
                    total = d['total_received'] / 10**8
                    unconfirmed = d['unconfirmed_balance'] / 10**8
                    return bal, total, unconfirmed
    except Exception as e:
        print(f"btc error: {e}")
    return None, None, None

async def get_eth_balance(address):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://api.blockcypher.com/v1/eth/main/addrs/{address}/balance', timeout=8) as r:
                if r.status == 200:
                    d = await r.json()
                    bal = int(d['balance']) / 10**18
                    total = int(d['total_received']) / 10**18
                    unconfirmed = int(d['unconfirmed_balance']) / 10**18
                    return bal, total, unconfirmed
    except Exception as e:
        print(f"eth error: {e}")
    return None, None, None

async def get_ltc_balance(address):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://api.blockcypher.com/v1/ltc/main/addrs/{address}/balance', timeout=8) as r:
                if r.status == 200:
                    d = await r.json()
                    bal = d['balance'] / 10**8
                    total = d['total_received'] / 10**8
                    unconfirmed = d['unconfirmed_balance'] / 10**8
                    return bal, total, unconfirmed
    except Exception as e:
        print(f"ltc error: {e}")
    return None, None, None

async def get_doge_balance(address):
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://api.blockcypher.com/v1/doge/main/addrs/{address}/balance', timeout=8) as r:
                if r.status == 200:
                    d = await r.json()
                    bal = d['balance'] / 10**8
                    total = d['total_received'] / 10**8
                    unconfirmed = d['unconfirmed_balance'] / 10**8
                    return bal, total, unconfirmed
    except Exception as e:
        print(f"doge error: {e}")
    return None, None, None

async def send_auto_message(message_id, channel_id, content, interval, repeat):
    while True:
        channel = bot.get_channel(channel_id)
        if channel is not None:
            await channel.send(content)
        if not repeat:
            break
        await asyncio.sleep(interval)

def start_auto_messages():
    for message_id, data in auto_messages.items():
        auto_message_tasks[message_id] = bot.loop.create_task(send_auto_message(message_id, **data))

async def status_rotation_loop():
    global status_rotation_active, status_rotation_data
    headers = {
        "Authorization": TOKEN,
        "User-Agent": "DiscordBot (https://discordapp.com , v1.0)",
        "Content-Type": "application/json",
        "Accept": "*/*"
    }
    
    while status_rotation_active:
        try:
            statuses = status_rotation_data.get("statuses", [])
            mode = status_rotation_data.get("current_mode", "online")
            
            if not statuses:
                await asyncio.sleep(30)
                continue
            
            for status_text in statuses:
                if not status_rotation_active:
                    break
                
                jsonData = {
                    "status": mode,
                    "custom_status": {
                        "text": status_text,
                    }
                }
                
                r = requests.patch("https://discord.com/api/v8/users/@me/settings", headers=headers, json=jsonData, timeout=5)
                if r.status_code == 200:
                    print(f"status changed to: {status_text}")
                else:
                    print(f"status change failed: {r.status_code}")
                
                await asyncio.sleep(10)
        except Exception as e:
            print(f"status rotation error: {e}")
            await asyncio.sleep(10)

def run_rpc(state, details, large_image, small_image=None, buttons=None):
    global rpc_client, rpc_active
    try:
        if rpc_client is None:
            rpc_client = Presence(1483979268810608701)
            rpc_client.connect()
        
        kwargs = {
            "state": state,
            "details": details,
            "large_image": large_image
        }
        
        if small_image:
            kwargs["small_image"] = small_image
        if buttons:
            kwargs["buttons"] = buttons
            
        rpc_client.update(**kwargs)
        rpc_active = True
        return True
    except Exception as e:
        print(f"rpc error: {e}")
        return False

def clear_rpc():
    global rpc_client, rpc_active
    try:
        if rpc_client:
            rpc_client.clear()
            rpc_client.close()
            rpc_client = None
        rpc_active = False
        return True
    except Exception as e:
        print(f"rpc clear error: {e}")
        return False

async def afk_cooldown(user_id, duration):
    afk_cooldowns[user_id] = True
    await asyncio.sleep(duration)
    if user_id in afk_cooldowns:
        del afk_cooldowns[user_id]

async def set_discord_status(status_mode):
    headers = {
        "Authorization": TOKEN,
        "User-Agent": "DiscordBot (https://discordapp.com , v1.0)",
        "Content-Type": "application/json",
        "Accept": "*/*"
    }
    jsonData = {"status": status_mode}
    try:
        r = requests.patch("https://discord.com/api/v8/users/@me/settings", headers=headers, json=jsonData, timeout=5)
        return r.status_code == 200
    except:
        return False

@bot.event
async def on_ready():
    print(f'logged in as {bot.user}')
    load_afk_data()
    load_auto_responses()
    load_auto_messages()
    load_status_rotation()
    start_auto_messages()
    
    global status_rotation_active, status_rotation_task
    if status_rotation_data.get("enabled", False):
        status_rotation_active = True
        status_rotation_task = bot.loop.create_task(status_rotation_loop())

@bot.event
async def on_message(msg):
    if msg.author == bot.user:
        await bot.process_commands(msg)
        return
        
    content_lower = msg.content.lower()
    for trigger, response in auto_responses.items():
        if trigger in content_lower:
            try:
                ch = bot.get_channel(msg.channel.id)
                if ch:
                    await ch.send(response)
            except Exception as e:
                print(f"ar send error: {e}")
            break
    
    for user_id, reason in afk_data.items():
        if f"<@{user_id}>" in msg.content or f"<@!{user_id}>" in msg.content:
            if msg.author.id not in afk_cooldowns:
                if isinstance(msg.channel, (discord.TextChannel, discord.DMChannel)):
                    await msg.channel.send(f"{msg.author.mention}, I am afk rn, **{reason}**")
                    await afk_cooldown(msg.author.id, 30)
            break
        elif msg.reference and msg.reference.message_id:
            try:
                replied_msg = await msg.channel.fetch_message(msg.reference.message_id)
                if str(replied_msg.author.id) == user_id:
                    if msg.author.id not in afk_cooldowns:
                        if isinstance(msg.channel, (discord.TextChannel, discord.DMChannel)):
                            await msg.channel.send(f"{msg.author.mention}, I am afk rn, **{reason}**")
                            await afk_cooldown(msg.author.id, 30)
                    break
            except:
                pass

    await bot.process_commands(msg)
    
    if active_reaction['enabled'] and active_reaction['emoji']:
        try:
            await msg.add_reaction(active_reaction['emoji'])
        except:
            try:
                await msg.add_reaction(active_reaction['emoji'].strip(':'))
            except:
                pass

@bot.command()
async def ping(ctx):
    await ctx.message.delete()
    lat = round(bot.latency * 1000)
    await ctx.send(f"pong {lat}ms", delete_after=5)

@bot.command()
async def track(ctx, *, addr=None):
    await ctx.message.delete()
    if not addr:
        await ctx.send("usage: .track <wallet_address> (btc, eth, ltc, doge)", delete_after=5)
        return
    
    crypto = detect_crypto(addr)
    if not crypto:
        await ctx.send("invalid address - supports btc, eth, ltc, doge", delete_after=5)
        return
    
    msg = await ctx.send(f"checking {crypto.upper()} balance...")
    
    price_task = get_crypto_price(supported_currencies.get(crypto, crypto))
    
    if crypto == 'btc':
        bal_task = get_btc_balance(addr)
    elif crypto == 'eth':
        bal_task = get_eth_balance(addr)
    elif crypto == 'ltc':
        bal_task = get_ltc_balance(addr)
    elif crypto == 'doge':
        bal_task = get_doge_balance(addr)
    else:
        await msg.edit(content="unsupported crypto", delete_after=5)
        return
    
    bal, total, unconfirmed = await bal_task
    price = await price_task
    
    if bal is not None and price is not None:
        resp = (
            f"**{crypto.upper()}**: `{addr}`\n"
            f"Balance: **{bal:.8f}** (${bal * price:.2f})\n"
            f"Total Received: **{total:.8f}** (${total * price:.2f})\n"
            f"Unconfirmed: **{unconfirmed:.8f}** (${unconfirmed * price:.2f})"
        )
        await msg.edit(content=resp)
    else:
        await msg.edit(content=f"couldnt fetch {crypto.upper()} balance", delete_after=5)

@bot.command()
async def msgdelete(ctx, amount: int = None):
    await ctx.message.delete()
    if not amount or amount < 1:
        await ctx.send("usage: .msgdelete <number>", delete_after=5)
        return
    if amount > 100:
        amount = 100
    
    deleted = 0
    async for message in ctx.channel.history(limit=amount):
        if message.author == bot.user:
            try:
                await message.delete()
                deleted += 1
                await asyncio.sleep(0.3)
            except:
                pass
    await ctx.send(f"deleted {deleted} messages", delete_after=5)

@bot.command()
async def avatar(ctx, *, member: discord.Member = None):
    await ctx.message.delete()
    if not member:
        member = ctx.author
    await ctx.send(str(member.avatar.url), delete_after=30)

@bot.command()
async def userinfo(ctx, user: discord.Member = None):
    await ctx.message.delete()
    if user is None:
        user = ctx.author
    date_format = "%a, %d %b %Y %I:%M %p"
    members = sorted(ctx.guild.members, key=lambda m: m.joined_at or ctx.guild.created_at)
    role_string = ', '.join([r.name for r in user.roles][1:])
    perm_string = ', '.join([str(p[0]).replace("_", " ").title() for p in user.guild_permissions if p[1]])
    info = (
        f"User: {user.mention}\n"
        f"Joined: {user.joined_at.strftime(date_format)}\n"
        f"Join position: {members.index(user) + 1}\n"
        f"Registered: {user.created_at.strftime(date_format)}\n"
        f"Roles: {len(user.roles) - 1}\n{role_string}\n"
        f"Perms: {perm_string}"
    )
    await ctx.send(info, delete_after=30)

@bot.command()
async def whois(ctx, user: discord.Member = None):
    await ctx.message.delete()
    if user is None:
        user = ctx.author
    headers = {'authorization': TOKEN, 'user-agent': 'Mozilla/5.0'}
    r = requests.get(f'https://discord.com/api/v9/users/{user.id}', headers=headers, timeout=5).json()
    banner_id = r.get("banner")
    if banner_id:
        banner_url = f"https://cdn.discord.com/banners/{user.id}/{banner_id}?size=1024"
    else:
        banner_url = "None"
    info = (
        f"User: {user.name}#{user.discriminator}\n"
        f"ID: {user.id}\n"
        f"Status: {user.status}\n"
        f"Bot: {user.bot}\n"
        f"Flags: {r.get('public_flags', 'None')}\n"
        f"Banner Color: {r.get('banner_color', 'None')}\n"
        f"Accent Color: {r.get('accent_color', 'None')}\n"
        f"Created: {user.created_at}\n"
        f"Avatar: {user.avatar.url}\n"
        f"Banner: {banner_url}"
    )
    await ctx.send(info, delete_after=30)

@bot.command()
async def stats(ctx):
    await ctx.message.delete()
    process = psutil.Process(os.getpid())
    ram_usage = process.memory_info().rss / 1024**2
    cpu_usage = psutil.cpu_percent()
    total_commands = len(bot.commands)
    info = (
        f"Sanction Self\n\n"
        f"Total cmds: {total_commands}\n"
        f"OS: {platform.system()}\n"
        f"RAM: {ram_usage:.2f} MB\n"
        f"CPU: {cpu_usage}%\n"
        f"Python: {platform.python_version()}"
    )
    await ctx.send(info, delete_after=30)

@bot.command()
async def tokeninfo(ctx, _token):
    await ctx.message.delete()
    headers = {'Authorization': _token, 'Content-Type': 'application/json'}
    try:
        res = requests.get('https://canary.discordapp.com/api/v9/users/@me', headers=headers, timeout=5).json()
        user_id = res['id']
        avatar_id = res['avatar']
        creation_date = f"<t:{int(((int(user_id) >> 22) + 1420070400000) / 1000)}:R>"
        nitro_type = "None"
        if "premium_type" in res:
            if res['premium_type'] == 2:
                nitro_type = "Nitro Boost"
            elif res['premium_type'] == 3:
                nitro_type = "Nitro Basic"
        msg = (
            f"Name: {res['username']}#{res['discriminator']}\n"
            f"ID: {res['id']}\n"
            f"Created: {creation_date}\n"
            f"Email: {res.get('email', 'Hidden')}\n"
            f"Phone: {res.get('phone', 'None')}\n"
            f"Flags: {res.get('flags', 'None')}\n"
            f"Lang: {res.get('locale', 'None')}\n"
            f"2FA: {res.get('mfa_enabled', 'None')}\n"
            f"Verified: {res.get('verified', 'None')}\n"
            f"Nitro: {nitro_type}\n"
            f"Avatar: https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}"
        )
        await ctx.send(msg, delete_after=30)
    except:
        await ctx.send("invalid token", delete_after=5)

@bot.command()
async def iplook(ctx, ip):
    await ctx.message.delete()
    api_key = 'a91c8e0d5897462581c0c923ada079e5'
    api_url = f'https://api.ipgeolocation.io/ipgeo?apiKey={api_key}&ip={ip}'
    try:
        data = requests.get(api_url, timeout=5).json()
        if 'country_name' in data:
            msg = (
                f"IP: {ip}\n"
                f"Country: {data['country_name']}\n"
                f"City: {data['city']}\n"
                f"ISP: {data['isp']}\n"
                f"Time: <t:{int(data['time_zone']['current_time_unix'])}:f>"
            )
            await ctx.send(msg, delete_after=30)
        else:
            await ctx.send("invalid ip", delete_after=5)
    except:
        await ctx.send("lookup failed", delete_after=5)

@bot.command()
async def id(ctx, *targets):
    await ctx.message.delete()
    if not targets:
        await ctx.send(f"your id: {ctx.author.id}", delete_after=5)
        return
    for target in targets:
        if target.lower() == "server":
            await ctx.send(f"server id: {ctx.guild.id}", delete_after=5)
        elif ctx.message.mentions:
            for member in ctx.message.mentions:
                await ctx.send(f"{member.name}: {member.id}", delete_after=5)
        elif ctx.message.channel_mentions:
            for channel in ctx.message.channel_mentions:
                await ctx.send(f"{channel.name}: {channel.id}", delete_after=5)
        elif ctx.message.role_mentions:
            for role in ctx.message.role_mentions:
                await ctx.send(f"{role.name}: {role.id}", delete_after=5)
        else:
            await ctx.send(f"cant find: {target}", delete_after=5)

@bot.command()
async def price(ctx, crypto='ltc'):
    await ctx.message.delete()
    if crypto not in supported_currencies:
        await ctx.send(f"supported: {', '.join(supported_currencies.keys())}", delete_after=5)
        return
    full = supported_currencies[crypto]
    try:
        price_val = await get_crypto_price(full)
        if price_val:
            await ctx.send(f"{crypto}: ${price_val}", delete_after=30)
        else:
            await ctx.send("failed to fetch price", delete_after=5)
    except:
        await ctx.send("failed to fetch price", delete_after=5)

@bot.command()
async def convert(ctx, amount: float, _from: str, _to: str):
    await ctx.message.delete()
    if _from not in supported_currencies or _to not in supported_currencies:
        await ctx.send(f"supported: {', '.join(supported_currencies.keys())}", delete_after=5)
        return
    from_full = supported_currencies[_from]
    to_full = supported_currencies[_to]
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(f'https://api.coingecko.com/api/v3/simple/price?ids={from_full},{to_full}&vs_currencies=usd', timeout=5) as r:
                data = await r.json()
                rate = data[from_full]['usd'] / data[to_full]['usd']
                result = amount * rate
                await ctx.send(f"{amount} {_from} = {result:.6f} {_to}", delete_after=30)
    except:
        await ctx.send("conversion failed", delete_after=5)

@bot.command()
async def credits(ctx):
    await ctx.message.delete()
    await ctx.send("made by @pissvad on discord", delete_after=30)

@bot.command()
async def afk(ctx, *, reason="busy so don't ping"):
    await ctx.message.delete()
    user_id = str(ctx.author.id)
    afk_data[user_id] = reason
    save_afk_data()
    await ctx.send("You are now AFK..", delete_after=5)

@bot.command()
async def unafk(ctx):
    await ctx.message.delete()
    user_id = str(ctx.author.id)
    if user_id in afk_data:
        del afk_data[user_id]
        save_afk_data()
        await ctx.send("You are no longer AFK", delete_after=5)
    else:
        await ctx.send("you are not AFK", delete_after=5)

@bot.command()
async def online(ctx):
    await ctx.message.delete()
    if await set_discord_status("online"):
        await ctx.send("status set to **online**", delete_after=5)
    else:
        await ctx.send("failed to set status", delete_after=5)

@bot.command()
async def idle(ctx):
    await ctx.message.delete()
    if await set_discord_status("idle"):
        await ctx.send("status set to **idle**", delete_after=5)
    else:
        await ctx.send("failed to set status", delete_after=5)

@bot.command()
async def dnd(ctx):
    await ctx.message.delete()
    if await set_discord_status("dnd"):
        await ctx.send("status set to **dnd**", delete_after=5)
    else:
        await ctx.send("failed to set status", delete_after=5)

@bot.command()
async def invisible(ctx):
    await ctx.message.delete()
    if await set_discord_status("invisible"):
        await ctx.send("status set to **invisible**", delete_after=5)
    else:
        await ctx.send("failed to set status", delete_after=5)

@bot.command()
async def offline(ctx):
    await ctx.message.delete()
    if await set_discord_status("invisible"):
        await ctx.send("status set to **offline**", delete_after=5)
    else:
        await ctx.send("failed to set status", delete_after=5)

@bot.command()
async def statusrotate(ctx, *, args=None):
    await ctx.message.delete()
    global status_rotation_active, status_rotation_task, status_rotation_data
    
    if args is None:
        if status_rotation_data.get("statuses"):
            statuses_text = "\n".join([f"• {s}" for s in status_rotation_data["statuses"]])
            mode = status_rotation_data.get("current_mode", "online")
            enabled = "ON" if status_rotation_active else "OFF"
            await ctx.send(f"**Status Rotation** ({enabled})\nMode: {mode}\n\nStatuses:\n{statuses_text}", delete_after=30)
        else:
            await ctx.send("no statuses set. use `.statusrotate add <text>` to add", delete_after=5)
        return
    
    args_parts = args.split(maxsplit=1)
    action = args_parts[0].lower()
    
    if action == "add":
        if len(args_parts) < 2:
            await ctx.send("usage: .statusrotate add <status text>", delete_after=5)
            return
        new_status = args_parts[1]
        if "statuses" not in status_rotation_data:
            status_rotation_data["statuses"] = []
        status_rotation_data["statuses"].append(new_status)
        save_status_rotation()
        await ctx.send(f"added status: {new_status}", delete_after=5)
    
    elif action == "remove":
        if len(args_parts) < 2:
            await ctx.send("usage: .statusrotate remove <index>", delete_after=5)
            return
        try:
            idx = int(args_parts[1])
            if 0 <= idx < len(status_rotation_data.get("statuses", [])):
                removed = status_rotation_data["statuses"].pop(idx)
                save_status_rotation()
                await ctx.send(f"removed status: {removed}", delete_after=5)
            else:
                await ctx.send("invalid index", delete_after=5)
        except ValueError:
            await ctx.send("usage: .statusrotate remove <index>", delete_after=5)
    
    elif action == "list":
        statuses = status_rotation_data.get("statuses", [])
        if not statuses:
            await ctx.send("no statuses set", delete_after=5)
            return
        resp = "**Status Rotation List:**\n\n"
        for i, status in enumerate(statuses):
            resp += f"[{i}] {status}\n"
        mode = status_rotation_data.get("current_mode", "online")
        resp += f"\nCurrent mode: {mode}"
        await ctx.send(resp, delete_after=30)
    
    elif action == "clear":
        status_rotation_data["statuses"] = []
        save_status_rotation()
        await ctx.send("all statuses cleared", delete_after=5)
    
    elif action == "mode":
        if len(args_parts) < 2:
            await ctx.send("usage: .statusrotate mode <online/idle/dnd/invisible>", delete_after=5)
            return
        mode = args_parts[1].lower()
        if mode not in ["online", "idle", "dnd", "invisible"]:
            await ctx.send("invalid mode. use: online, idle, dnd, invisible", delete_after=5)
            return
        status_rotation_data["current_mode"] = mode
        save_status_rotation()
        await ctx.send(f"rotation mode set to **{mode}**", delete_after=5)
    
    elif action == "on":
        if not status_rotation_data.get("statuses"):
            await ctx.send("no statuses to rotate. add some first with `.statusrotate add`", delete_after=5)
            return
        if status_rotation_active:
            await ctx.send("status rotation already running", delete_after=5)
            return
        status_rotation_active = True
        status_rotation_data["enabled"] = True
        save_status_rotation()
        status_rotation_task = bot.loop.create_task(status_rotation_loop())
        await ctx.send("status rotation **started**", delete_after=5)
    
    elif action == "off":
        if not status_rotation_active:
            await ctx.send("status rotation not running", delete_after=5)
            return
        status_rotation_active = False
        status_rotation_data["enabled"] = False
        save_status_rotation()
        if status_rotation_task:
            status_rotation_task.cancel()
        await ctx.send("status rotation **stopped**", delete_after=5)
    
    else:
        await ctx.send("usage: .statusrotate <add/remove/list/clear/mode/on/off>", delete_after=5)

@bot.command()
async def rpc(ctx, *, args=None):
    await ctx.message.delete()
    global rpc_active
    
    if args is None:
        await ctx.send("usage: .rpc <state> | <details> | <large_image_url> | <small_image_url (optional)> or .rpc off", delete_after=5)
        return
    
    if args.lower() == "off":
        if clear_rpc():
            await ctx.send("rpc cleared", delete_after=5)
        else:
            await ctx.send("rpc not active", delete_after=5)
        return
    
    parts = [p.strip() for p in args.split('|')]
    
    if len(parts) < 3:
        await ctx.send("usage: .rpc <state> | <details> | <large_image_url> | <small_image_url (optional)>", delete_after=5)
        return
    
    state = parts[0]
    details = parts[1]
    large_image = parts[2]
    small_image = parts[3] if len(parts) > 3 else None
    
    success = run_rpc(state, details, large_image, small_image)
    
    if success:
        await ctx.send(f"rpc set\nstate: {state}\ndetails: {details}", delete_after=5)
    else:
        await ctx.send("failed to set rpc - make sure discord is open", delete_after=5)

@bot.command()
async def harmlevel(ctx):
    await ctx.message.delete()
    level = random.randint(1, 100)
    
    if level < 25:
        msg = "low threat"
    elif level < 50:
        msg = "moderate threat"
    elif level < 75:
        msg = "high threat"
    elif level < 90:
        msg = "critical threat"
    else:
        msg = "MAXIMUM THREATTTT"
    
    await ctx.send(f"harmful level: **{level}%** - {msg}", delete_after=10)

@bot.command()
async def terryquote(ctx):
    await ctx.message.delete()
    quote = random.choice(terry_quotes)
    await ctx.send(f"**Terry A. Davis:** {quote}", delete_after=30)

@bot.command()
async def gif(ctx, *, source=None):
    await ctx.message.delete()
    
    image_url = None
    
    if ctx.message.attachments:
        image_url = ctx.message.attachments[0].url
    elif ctx.message.reference:
        try:
            replied_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            if replied_msg.attachments:
                image_url = replied_msg.attachments[0].url
            elif replied_msg.embeds:
                image_url = replied_msg.embeds[0].url or replied_msg.embeds[0].image.url
        except:
            pass
    elif source:
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
            image_url = str(user.avatar.url)
        else:
            image_url = source.strip()
    
    if not image_url:
        await ctx.send("usage: .gif <image_url> or attach an image or reply to an image", delete_after=5)
        return
    
    msg = await ctx.send("converting to gif...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url, timeout=15) as resp:
                if resp.status != 200:
                    await msg.edit(content="failed to download image", delete_after=5)
                    return
                image_data = await resp.read()
        
        image = Image.open(io.BytesIO(image_data))
        
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            if image.mode in ('RGBA', 'LA'):
                background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = background
            else:
                image = image.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        gif_buffer = io.BytesIO()
        image.save(gif_buffer, format='GIF', optimize=True)
        gif_buffer.seek(0)
        
        await msg.delete()
        await ctx.send(file=discord.File(fp=gif_buffer, filename='converted.gif'))
        
    except Exception as e:
        print(f"gif conversion error: {e}")
        await msg.edit(content=f"conversion failed: {str(e)[:50]}", delete_after=5)

P = '\u001b[35m'
BP = '\u001b[1;35m'

def purpletxt(txt):
    out = ''
    for c in txt:
        if c.isalpha():
            out += f'{P}{c}{W}'
        else:
            out += c
    return out

@bot.command(aliases=['cmds'])
async def helpcmd(ctx):
    await ctx.message.delete()
    em = active_reaction['emoji'] or 'None'
    st = 'ON' if active_reaction['enabled'] else 'OFF'
    sc = LG if active_reaction['enabled'] else LR
    rpc_st = 'ON' if rpc_active else 'OFF'
    rpc_sc = LG if rpc_active else LR
    afk_st = 'ON' if str(ctx.author.id) in afk_data else 'OFF'
    afk_sc = LG if str(ctx.author.id) in afk_data else LR
    rot_st = 'ON' if status_rotation_active else 'OFF'
    rot_sc = LG if status_rotation_active else LR
    
    msg = f"""```ansi
{BP} ▄█     █▄     ▄████████ ████████▄  ████████▄   ▄█          ▄████████ 
{BP}███     ███   ███    ███ ███   ▀███ ███   ▀███ ███         ███    ███ 
{BP}███     ███   ███    ███ ███    ███ ███    ███ ███         ███    █▀  
{BP}███     ███   ███    ███ ███    ███ ███    ███ ███        ▄███▄▄▄     
{BP}███     ███ ▀███████████ ███    ███ ███    ███ ███       ▀▀███▀▀▀     
{BP}███     ███   ███    ███ ███    ███ ███    ███ ███         ███    █▄  
{BP}███ ▄█▄ ███   ███    ███ ███   ▄███ ███   ▄███ ███▌    ▄   ███    ███ 
{BP} ▀███▀███▀    ███    █▀  ████████▀  ████████▀  █████▄▄██   ██████████ 
{BP}                                               ▀                      {W}

{bluetxt("Main:")} {purpletxt(".react")} {B}<e>{W} | {purpletxt(".ping")} | {purpletxt(".msgdelete")} {B}<n>{W} | {purpletxt(".rpc")} | {purpletxt(".gif")}

{bluetxt("Status:")} {purpletxt(".online/.idle/.dnd/.invisible")} | {purpletxt(".statusrotate")} {B}<add/rem/list/on/off>{W}

{bluetxt("User:")} {purpletxt(".avatar/.userinfo/.whois/.id")} {B}<@user>{W}

{bluetxt("Crypto:")} {purpletxt(".track")} {B}<wallet>{W} | {purpletxt(".price/.convert")}

{bluetxt("Tools:")} {purpletxt(".tokeninfo/.iplook/.stats")}

{bluetxt("AFK:")} {purpletxt(".afk/.unafk")}

{bluetxt("Auto:")} {purpletxt(".addar/.delar/.listar")} | {purpletxt(".startauto/.listauto/.stopauto")}

{bluetxt("Other:")} {purpletxt(".credits/.harmlevel/.terryquote/.cmds")}

{BP}Status:{W} {P}{em}{W} | {sc}{st}{W} | rpc:{rpc_sc}{rpc_st}{W} | afk:{afk_sc}{afk_st}{W} | rot:{rot_sc}{rot_st}{W}
```"""
    await ctx.send(msg, delete_after=30)

@bot.command()
async def react(ctx, emo=None):
    await ctx.message.delete()
    if not emo:
        await ctx.send("use .react <emoji> or .react off", delete_after=5)
        return
    if emo.lower() == 'off':
        active_reaction['enabled'] = False
        active_reaction['emoji'] = None
        await ctx.send("auto react off", delete_after=5)
        return
    m = re.match(r':?([^:]+):?', emo)
    e = m.group(1) if m else emo
    active_reaction['emoji'] = e
    active_reaction['enabled'] = True
    await ctx.send(f"now reacting with :{e}:", delete_after=5)

@bot.command(name='addar', aliases=['aa'])
async def addar(ctx, trigger: str, *, response: str):
    await ctx.message.delete()
    trigger = trigger.lower()
    if trigger in auto_responses:
        await ctx.send("auto response already exists", delete_after=5)
        return
    auto_responses[trigger] = response
    save_auto_responses()
    await ctx.send("ar added", delete_after=5)

@bot.command(name='delar', aliases=['ra', 'removear'])
async def delar(ctx, trigger: str):
    await ctx.message.delete()
    trigger = trigger.lower()
    if trigger not in auto_responses:
        await ctx.send("no ar found", delete_after=5)
        return
    auto_responses.pop(trigger)
    save_auto_responses()
    await ctx.send("ar deleted", delete_after=5)

@bot.command(name='listar', aliases=['la'])
async def listar(ctx):
    await ctx.message.delete()
    if not auto_responses:
        await ctx.send("no auto responses", delete_after=5)
        return
    resp = "auto responses:\n\n"
    for trigger, response_text in auto_responses.items():
        resp += f"**{trigger}** -> `{response_text}`\n"
    await ctx.send(resp, delete_after=30)

@bot.command(name='startauto', aliases=['am'])
async def startauto(ctx, interval: int = None, repeat: str = None, channel: discord.TextChannel = None, *, content: str = None):
    await ctx.message.delete()
    if not all([interval, repeat, channel, content]):
        await ctx.send("usage: .startauto <seconds> <true/false> <#channel> <message>", delete_after=5)
        return
    repeat_bool = repeat.lower() in ['true', 'yes', '1', 't']
    message_id = str(ctx.message.id)
    data = {
        "channel_id": channel.id,
        "content": content,
        "interval": interval,
        "repeat": repeat_bool,
    }
    auto_messages[message_id] = data
    auto_message_tasks[message_id] = bot.loop.create_task(send_auto_message(message_id, **data))
    save_auto_messages()
    await ctx.send(f"auto msg started (id: {message_id})", delete_after=5)

@bot.command(name='listauto', aliases=['lam'])
async def listauto(ctx):
    await ctx.message.delete()
    if not auto_messages:
        await ctx.send("no auto messages", delete_after=5)
        return
    resp = "auto messages:\n\n"
    for message_id, data in auto_messages.items():
        channel = bot.get_channel(data["channel_id"])
        ch_name = channel.name if channel else "unknown"
        rep = "yes" if data["repeat"] else "no"
        resp += f"id: {message_id} | ch: {ch_name} | {data['interval']}s | repeat: {rep}\n"
    await ctx.send(resp, delete_after=30)

@bot.command(name='stopauto', aliases=['sam'])
async def stopauto(ctx, message_id: int):
    await ctx.message.delete()
    str_id = str(message_id)
    if str_id not in auto_messages:
        await ctx.send("no auto msg with that id", delete_after=5)
        return
    if str_id in auto_message_tasks:
        auto_message_tasks[str_id].cancel()
        del auto_message_tasks[str_id]
    del auto_messages[str_id]
    save_auto_messages()
    await ctx.send("auto msg stopped", delete_after=5)

bot.run(TOKEN)
