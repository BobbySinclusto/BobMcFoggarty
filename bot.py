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
import ctypes

import asyncio
import threading

from concurrent.futures import ThreadPoolExecutor

import io
import aiohttp

from PIL import Image
from googleapiclient.discovery import build

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
SCRIPTS_PATH = os.getenv('SCRIPTS_PATH')
SERVER_ADDRESS = os.getenv('SERVER_ADDRESS')
SERVER_PORT = os.getenv('SERVER_PORT')
WOLFRAM_API_KEY = os.getenv('WOLFRAM_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
GOOGLE_SE_ID = os.getenv('GOOGLE_SE_ID')

try:
    wolfram_client = wolframalpha.Client(WOLFRAM_API_KEY)
except:
    pass

current_world = open(SCRIPTS_PATH + 'currentworld.txt', 'r').read().strip()
funfacts = open('dyk.txt', 'r').readlines()
server_process = 0
ngrok_process = 0
addr = ''
current_players = set()
waiting_command_response = False
cmd_ctx = None
waiting_for_start = False
waiting_for_stop = False

bot = commands.Bot(command_prefix='!')
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user} has connected to the following guild:\n'
          f'{guild.name}(id: {guild.id})'
    )

    members = '\n - '.join([str(member.id) + ' ' + member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')
    game = discord.Game('ngrok')
    await bot.change_presence(status=discord.Status.online, activity=game)

@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(f'Hi {member.name}, welcome to the Nerd Herd!')

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    return res['items']

@bot.event
async def on_message(message):
    global addr
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    print(message.content)
    #if message.channel.id == 789625114769621003:
    if message.channel.id == 836413232700719105:
        # send a message on the minecraft server
        if addr != '':
            server_process.stdin.write(('/tellraw @a {\"text\":\"<' + message.author.display_name + ' (Discord)> ' + message.content + '\"}\n').encode())
            server_process.stdin.flush()

    msg = message.content.lower()
    if re.search(r'\b[Bb]ob\b', msg) != None:
        questions = ['hey bob', '?', 'who', 'what', 'when', 'where', 'why', 'how', 'which']
        if any(q in msg for q in questions):
            try:
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

''' MINECRAFT SERVER THINGS '''
async def output_reader(proc, loop):
    global current_players
    global waiting_command_response
    global cmd_ctx
    global waiting_for_start
    global waiting_for_stop
    global addr

    message = None
    io_pool_exc = ThreadPoolExecutor()

    while True:
        try:
            if waiting_for_stop:
                waiting_for_stop = False
                return
            line = await loop.run_in_executor(io_pool_exc, proc.stdout.readline)

            current = line.decode('utf-8')

            if not bot.is_closed():
                player_message = re.search(r'^\[.*\] \[.*\]: (<.*>.*)$', current)
                if player_message != None:
                    #await bot.get_channel(789625114769621003).send(player_message.groups()[0])
                    #await bot.get_channel(761382066360680448).send(player_message.groups()[0])
                    await bot.get_channel(836413232700719105).send(player_message.groups()[0])

                player_joined = re.search(r': (.*) joined the game', current)
                if player_joined != None:
                    #await bot.get_channel(789625114769621003).send(player_joined.groups()[0] + ' joined the game')
                    #await bot.get_channel(761382066360680448).send(player_joined.groups()[0] + ' joined the game')            
                    await bot.get_channel(836413232700719105).send(player_joined.groups()[0] + ' joined the game')            
                    try:
                        current_players.add(player_joined.groups()[0])
                    except:
                        pass

                player_left = re.search(r': (.*) left the game', current)
                if player_left != None:
                    #await bot.get_channel(789625114769621003).send(player_left.groups()[0] + ' left the game')
                    #await bot.get_channel(761382066360680448).send(player_left.groups()[0] + ' left the game')
                    await bot.get_channel(836413232700719105).send(player_left.groups()[0] + ' left the game')
                    try:
                        current_players.remove(player_left.groups()[0])
                    except:
                        pass

                if waiting_command_response:
                    waiting_command_response = False
                    await cmd_ctx.send(current)

                if waiting_for_start and message == None:
                    message = await cmd_ctx.send('```m\n' + current + '```')
                elif waiting_for_start:
                    await message.edit(content=('```m\n' + current + '```'))
                    if re.search(r'Done \(.*\)!', current):
                        waiting_for_start = False
                        message = None
                        await cmd_ctx.send('Success! Server address: ' + addr)
                    

            print(current, end='')
        except:
            return

@bot.command(name='startserver', help='Starts the server')
async def startserver(ctx):
    global server_process
    global ngrok_process
    global addr
    global waiting_for_start
    global cmd_ctx

    if addr != '':
        await ctx.send('The server is running already! Server address: ' + addr + '\n\nIf you are at Austin\'s house, use 192.168.0.113:25566 instead.')
        return
    await ctx.send('Starting server...')
        
    server_process = subprocess.Popen(['java', '-Xmx10g', '-Xms10g', '-jar', 'server.jar', 'nogui'], cwd=SCRIPTS_PATH, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    print('opened process')

    bot.loop.create_task(output_reader(server_process, bot.loop))
    print('output_reader created')
    #bot.loop.create_task(my_background_task(ctx, server_process))
    # there used to be an input thread here but it was causing problems so I removed it

    if SERVER_ADDRESS == None:
        ngrok_process = subprocess.Popen([SCRIPTS_PATH + 'ngrok', 'tcp', str(SERVER_PORT)], cwd=SCRIPTS_PATH, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            try:
                time.sleep(2)
                j = requests.get('http://127.0.0.1:4040/api/tunnels').json()
                addr = j['tunnels'][0]['public_url'][6:]
                break
            except:
                pass
    else:
        addr = SERVER_ADDRESS

    # Wait for server to start
    waiting_for_start = True
    cmd_ctx = ctx

@bot.command(name='onlineplayers', help='Displays the players that are currently online')
async def onlineplayers(ctx):
    global current_players

    try:
        if len(current_players) != 0:
            await ctx.send('```' + '\n'.join(current_players) + '```')
        else:
            await ctx.send('No one is playing right now')
    except Exception as e:
        print(e)

@bot.command(name='sendmccommand', help='sends a command to the server')
async def sendmccommand(ctx, *args):
    global waiting_command_response
    global cmd_ctx
    global server_process

    try:
        server_process.stdin.write((' '.join(args) + '\n').encode())
        server_process.stdin.flush()
        cmd_ctx = ctx
        waiting_command_response = True
    except Exception as e:
        print(e)

@bot.command(name='currentconfig', help='Displays the current server config')
async def currentconfig(ctx):
    await ctx.send('```sh\n'+''.join(open(SCRIPTS_PATH + 'server.properties').readlines())+'```')

@bot.command(name='updateconfig', help='Updates server.properties')
async def updateconfig(ctx, *args):
    try:
        # get current properties
        p_file = open(SCRIPTS_PATH + 'server.properties', 'r')
        header = p_file.readline()
        header += p_file.readline()
        properties = {key:value for key, value in [line.split('=') for line in p_file.readlines()]}
        p_file.close()

        for key in properties:
            if key == args[0]:
                properties[key] = ' '.join(args[1:]) + '\n'
                p_file = open(SCRIPTS_PATH + 'server.properties', 'w')
                p_file.write(header + ''.join([key + '=' + properties[key] for key in properties]))
                p_file.close()
                await ctx.send('Successfully updated `' + key + '` to `' + ' '.join(args[1:]) + '`!')
                return
        
        await ctx.send('Invalid config item: `' + args[0] + '`')
        
    except Exception as e:
        print(e)
        await ctx.send('You done made an oops in that command buddy. Try again')
    




@bot.command(name='currentworld', help='Displays the currently selected world')
async def currentworld(ctx):
    await ctx.send('Current world: ' + current_world)

@bot.command(name='serveraddress', help='Displays the server address')
async def serveraddress(ctx):
    global addr
    if addr == '':
        await ctx.send('The server is not running yet. Use !startserver to start it!')
    else:
        await ctx.send(addr)

@bot.command(name='saveworld', help='Backs up the current world to the world in the list')
async def saveworld(ctx):
    subprocess.call('rm -rf ' + SCRIPTS_PATH + '../Worlds/' + current_world.replace(' ', '\\ ').replace('\'', '\\\'') + '.bak', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True) 
    subprocess.call('cp -r ' + SCRIPTS_PATH + '../Worlds/' + current_world.replace(' ', '\\ ').replace('\'', '\\\'') + ' ' + SCRIPTS_PATH + '../Worlds/' + current_world.replace(' ', '\\ ').replace('\'', '\\\'') + '.bak', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True) 
    subprocess.call('rm -rf ' + SCRIPTS_PATH + '../Worlds/' + current_world.replace(' ', '\\ ').replace('\'', '\\\'') + '/*', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True) 
    subprocess.call('cp -r ' + SCRIPTS_PATH + 'world/* ' + SCRIPTS_PATH + '../Worlds/' + current_world.replace(' ', '\\ ').replace('\'', '\\\'') + '/', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True) 
    await ctx.send('World backed up successfully!')

@bot.command(name='stopserver', help='Stops the server')
async def stopserver(ctx):
    global addr
    global current_players
    global waiting_for_stop
    waiting_for_stop = True
    current_players = set()
    try:
        server_process.communicate(input=b'/stop\n')
        '''
        if SERVER_ADDRESS == None:
            ngrok_process.terminate()
        '''
        addr = ''

        await ctx.send('Server stopped.')
        if current_world == 'newworld':
            await saveworld(ctx)
    except Exception as e:
        print(e)
        await ctx.send('You can\'t stop a server that hasn\'t been started. Use !startserver to start the server!')

@bot.command(name='resetworld', help='Resets world to its last saved state')
async def resetworld(ctx):
    global server_process
    global addr
    await ctx.send('Resetting the world...')
    try:
        server_process.communicate(input=b'/stop\n')
    except:
        print(sys.exc_info()[0])
        pass
    subprocess.call('rm -rf ' + SCRIPTS_PATH + 'world/*', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True)
    subprocess.call(['ls', SCRIPTS_PATH + 'world'])
    subprocess.call('cp -r ' + SCRIPTS_PATH + '../Worlds/' + current_world.replace(' ', '\\ ').replace('\'', '\\\'') + '/* ' + SCRIPTS_PATH + 'world/', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True) 
    if addr == '':
        await ctx.send('The server isn\'t started! Use !startserver to start the server.')
        return
    await ctx.send('The server is restarting...')
    addr = ''
    await startserver(ctx)

@bot.command(name='listworlds', help='Lists the worlds that have been added')
async def listworlds(ctx):
    p = subprocess.run(['ls', SCRIPTS_PATH + '../Worlds/'], stdout=subprocess.PIPE)
    msg = '```'
    worlds = p.stdout.decode("utf-8").split('\n')
    for i in range(1, len(worlds)):
        msg += str(i) + '. ' + (' ' if i < 10 else '') + worlds[i - 1] + '\n'
    msg += '```'
    await ctx.send(msg)

@bot.command(name='selectworld', help='Selects a world, by world name or world number. Use double quotes around a world name, or a world number from the list of worlds.')
async def selectworld(ctx, world):
    try:
        global current_world
        p = subprocess.run(['ls', SCRIPTS_PATH + '../Worlds/'], stdout=subprocess.PIPE)
        worlds = p.stdout.decode("utf-8").split('\n')

        idx = -1
        try:
            idx = int(world) - 1
        except:
            for i in range(len(worlds)-1):
                if world == worlds[i]:
                    idx = i

        if idx < 0 or idx > len(worlds) - 2:
            await ctx.send('Invalid input.')
        else:
            if current_world == 'newworld':
                await saveworld(ctx)
            current_world = worlds[idx]
            f = open(SCRIPTS_PATH + 'currentworld.txt', 'w')
            f.write(worlds[idx])
            await ctx.send('Selected world: ' + worlds[idx])
            await resetworld(ctx)
            print('select world')
    except Exception as e:
        print(e)

@bot.command(name='addworld', help='Adds a world from a link to a zip file.')
async def addworld(ctx, link):
    await ctx.send('Attempting to download world...')
    try:
        subprocess.run(['mkdir', SCRIPTS_PATH + 'blorgle'])
        r = requests.get(link, allow_redirects=True)
        open(SCRIPTS_PATH + 'blorgle/download.zip', 'wb').write(r.content)
        p = subprocess.run(['unzip', SCRIPTS_PATH + 'blorgle/download.zip'], cwd=SCRIPTS_PATH + 'blorgle/', stdout=subprocess.PIPE)
        if p.returncode == 0:
            world = ''
            path = ''
            output = p.stdout.decode('utf-8').split('\n')
            for i in range(len(output)):
                output[i] = output[i].strip()
                match = re.compile('[/| ][^/]*/region').search(output[i])
                if match != None:
                    world = output[i][match.start() + 1 : match.end() - 7]
                    path = SCRIPTS_PATH + 'blorgle/' + output[i][10:match.end() - 7].replace(' ', '\\ ').replace('\'', '\\\'')
                    break
            if world == '':
                await ctx.send('Not a valid Minecraft world :-(')
            else:
                subprocess.run('mv ' + path + ' ' + SCRIPTS_PATH + '../Worlds/', shell=True)
                await ctx.send(world + '\nImported successfully!')
                await ctx.send('Use !selectworld \"' + world + '\" to select it.')
        else:
            await ctx.send('File was not a zip archive :-(')
    except:
        await ctx.send('Unable to download file from url :-(')
        pass
    subprocess.run(['rm', '-rf', SCRIPTS_PATH + 'blorgle'])

@bot.command(name='funfact', help='Displays a fun fact.')
async def funfact(ctx):
    await ctx.send('Did you know ' + random.choice(funfacts))

for i in range(1000):
    try:
        bot.run(TOKEN)
    except Exception as e:
        print(e)
        time.sleep(5)
        print('\nBot crashed, restarting...')

print('Reached maximum number of retries. Something went wrong.')
