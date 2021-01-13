import os
import subprocess
import sys
import re
import requests
import discord
import json
import time
import random
from discord.ext import commands
from dotenv import load_dotenv
import wolframalpha

import io
import aiohttp

from PIL import Image
from googleapiclient.discovery import build

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
WOLFRAM_API_KEY = os.getenv('WOLFRAM_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_SE_ID = os.getenv('GOOGLE_SE_ID')

try:
    wolfram_client = wolframalpha.Client(WOLFRAM_API_KEY)
except:
    pass

funfacts = open('dyk.txt', 'r').readlines()

bot = commands.Bot(command_prefix='!')
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user} has connected to the following guild:\n'
          f'{guild.name}(id: {guild.id})'
    )

    members = '\n - '.join([str(member.id) + ' ' + member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')
    game = discord.Game('Wolfram|Alpha')
    await bot.change_presence(status=discord.Status.online, activity=game)

@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f'Hi {member.name}, welcome to Hacky Stack!')

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    print(message.content)
    msg = message.content.lower()
    if 'bob' in msg:
        questions = ['hey bob', '?', 'who', 'what', 'when', 'where', 'why', 'how', 'which']
        if any(q in msg for q in questions):
            try:
                if 'image' in msg:
                    raise Exception('use google')
                msg = msg.replace('hey bob, ', '').replace('hey bob', '').replace(', bob', '').replace('bob', '').replace('?', '') 
                res = wolfram_client.query(msg)
                try:
                    await message.channel.send(next(res.results).text.replace('Wolfram|Alpha', 'Bob McFoggarty'))
                except:
                    pass
                
                async with aiohttp.ClientSession() as session:
                    for p in res.pods:
                        for s in p.subpods:
                            try:
                                async with session.get(s['img']['@src']) as resp:
                                    if resp.status == 200:
                                        data = io.BytesIO(await resp.read())
                                        await message.channel.send(file=discord.File(data, 'result.png'))
                            except:
                                pass
                        
            except:
                try:
                    msg = msg.replace('hey bob, ', '').replace('hey bob', '').replace(', bob', '').replace('bob', '').replace('?', '') 
                    if 'image' in msg or 'animated gif' in msg:
                        results = google_search(msg + ' filetype:png OR filetype:gif OR filetype:jpg OR filetype:jpeg', GOOGLE_API_KEY, GOOGLE_SE_ID, searchType='image', num=10)
                        async with aiohttp.ClientSession() as session:
                            random.shuffle(results)
                            for result in results:
                                print('started trying')
                                try:
                                    async with session.get(result['link']) as resp:
                                        if resp.status == 200:
                                            data = io.BytesIO(await resp.read())
                                            print('started sending ' + result['fileFormat'])

                                            await message.channel.send(file=discord.File(data, 'result.' + re.search(r'image/(.+$)', result['fileFormat']).groups()[0]))
                                        else:
                                            raise Exception('unable to get image')
                                        return
                                except Exception as e:
                                    print(e)
                    else:
                        results = google_search(msg, GOOGLE_API_KEY, GOOGLE_SE_ID, num=1)
                        for result in results:
                            print(result)
                            await message.channel.send(result['snippet'])
                    return

                except Exception as e:
                    print(e)

                members = [133636765649993729, 236675869643505665, 346401802910040076, 348596653735018496, 472165066670735363, 487262355546177536, 604427812895588363]
                opt = random.randrange(3)
                if opt == 0:
                    await message.channel.send('No idea. Come up with a better question and try again lol\nDid you know ' + random.choice(funfacts))
                elif opt == 1:
                    await message.channel.send('You\'ll have to ask ' + '<@' + str(random.choice(members)) + '> on that one')
                else:
                    if 'is' in msg:
                        await message.channel.send('I don\'t know, ' + msg.replace('is', '***is***') + '???')
                    else:
                        await message.channel.send('Sorry, I\'ve got better things to do right now')
        else:
            answers = ['I live to serve.', 'I aim to please.', 'I\'m a bot. beep boop.']
            await message.channel.send(random.choice(answers))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandNotFound):
        await ctx.send('Command not found. Type !help for list of commands.')
    else:
        await ctx.send('Error processing command. See !help for command usage instructions.')
    await ctx.send('Did you know ' + random.choice(funfacts))

async def make_ban_img(user_img):
    ban_imgs = [Image.open('assets/ban%d.png' % (i+1)).convert('RGBA') for i in range(5)]

    # new size is 60x60, starts at 150, 159


    avatar_img = Image.open(user_img)
    avatar_img = avatar_img.resize((60, 60))

    avatar_img_r = Image.new(avatar_img.mode, (ban_imgs[0].width, ban_imgs[1].height))
    avatar_img_r.paste(avatar_img, (150, 159))# 210, 219))
    avatar_img_r.putpalette(avatar_img.palette.getdata()[1])

    frames = []

    for frame in ban_imgs:
        to_cover = avatar_img_r.convert('RGBA')
        to_cover.paste(frame, mask=frame)
        frames.append(to_cover)

    out = io.BytesIO()

    frames[0].save(out, 'gif', save_all=True, append_images=frames[1:], loop=0, duration=90)
    print('opened images')
    out.seek(0)
    return out


@bot.command(name='ban', help='bans a member from the server')
async def ban(ctx, *args):
    try:
        userids = [int(r) for r in re.findall(r'<@!{,1}([0-9]*)>', ' '.join(args))]
        for userid in userids:
            user = None
            async for member in ctx.guild.fetch_members(limit=None):
                if member.id == userid:
                    user = member
                    break

            pfp = str(user.avatar_url).split('?size=')[0]
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(pfp) as resp:
                        print(resp)
                        if resp.status == 200:
                            original_img = io.BytesIO(await resp.read())
                            pil_img = Image.open(original_img)
                            pil_img.info.pop('background', None)
                            data = io.BytesIO()
                            pil_img.save(data, 'gif')
                            data.seek(0)

                            res = await make_ban_img(data)

                            print('got image')
                            await ctx.channel.send(file=discord.File(res, 'result.gif'))
                            print('sent')
                        else:
                            raise Exception('download failed')
                except:
                    pass
        
    except Exception as e:
        await ctx.send('Banned.')
        print(e)

@bot.command(name='ping', help='pong!')
async def ping(ctx):
    await ctx.send('pong!')

@bot.command(name='funfact', help='Displays a fun fact.')
async def funfact(ctx):
    await ctx.send('Did you know ' + random.choice(funfacts))

bot.run(TOKEN)
