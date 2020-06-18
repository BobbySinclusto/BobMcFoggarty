import os
import subprocess
import sys
import re
import requests
import discord
import json
import time
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
SCRIPTS_PATH = os.getenv('SCRIPTS_PATH')
SERVER_ADDRESS = os.getenv('SERVER_ADDRESS')
SERVER_PORT = os.getenv('SERVER_PORT')

current_world = open(SCRIPTS_PATH + 'currentworld.txt', 'r').read().strip();
server_process = 0
ngrok_process = 0
addr = ''

bot = commands.Bot(command_prefix='!')
@bot.event
async def on_ready():
    guild = discord.utils.get(bot.guilds, name=GUILD)
    print(f'{bot.user} has connected to the following guild:\n'
          f'{guild.name}(id: {guild.id})'
    )

    members = '\n - '.join([member.name for member in guild.members])
    print(f'Guild Members:\n - {members}')
    game = discord.Game('ngrok')
    await bot.change_presence(status=discord.Status.online, activity=game)

@bot.event
async def on_member_join(member):
    await member.create_dm()
    await member.dm_channel.send(
            f'Hi {member.name}, welcome to the Nerd Herd!'
    )

@bot.event
async def on_message(message):
    await bot.process_commands(message)
    if message.author == bot.user:
        return
    print(message.content)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.CommandNotFound):
        await ctx.send('Command not found. Type !help for list of commands.')
    else:
        raise error

@bot.command(name='ping', help='pong!')
async def ping(ctx):
    await ctx.send('pong!')

@bot.command(name='startserver', help='Starts the server')
async def startserver(ctx):
    global server_process
    global ngrok_process
    global addr
    if addr != '':
        await ctx.send('The server is running already! Server address: ' + addr)
        return
    await ctx.send('Starting server...')
        
    server_process = subprocess.Popen(['java', '-Xmx1024M', '-Xms1024M', '-jar', 'server.jar', 'nogui'], cwd=SCRIPTS_PATH, stdin=subprocess.PIPE) 
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
    await ctx.send('Success! Server address: ' + addr)

@bot.command(name='currentworld', help='Displays the currently selected world')
async def currentworld(ctx):
    await ctx.send('Current world: ' + current_world)

@bot.command(name='serveraddress', help='Displays the server address')
async def serveraddress(ctx):
    if addr == '':
        await ctx.send('The server is not running yet. Use !startserver to start it!')
    else:
        await ctx.send(addr)

@bot.command(name='stopserver', help='Stops the server')
async def stopserver(ctx):
    global addr
    try:
        server_process.communicate(input=b'/stop\n')
        if SERVER_ADDRESS == None:
            ngrok_process.terminate()
        addr = ''
        await ctx.send('Server stopped.')
    except:
        await ctx.send('You can\'t stop a server that hasn\'t been started. Use !startserver to start the server!')

@bot.command(name='resetworld', help='Resets world to its original state')
async def resetworld(ctx):
    global server_process
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
    server_process = subprocess.Popen(['java', '-Xmx1024M', '-Xms1024M', '-jar', 'server.jar', 'nogui'], cwd=SCRIPTS_PATH, stdin=subprocess.PIPE)
    await ctx.send('The server is restarting...')
    time.sleep(5)
    await ctx.send('Success! Server address: ' + addr)

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
        current_world = worlds[idx]
        f = open(SCRIPTS_PATH + 'currentworld.txt', 'w')
        f.write(worlds[idx])
        await ctx.send('Selected world: ' + worlds[idx])
        await resetworld(ctx)
        print('select world')

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
                subprocess.run(['mv', path, SCRIPTS_PATH + '../Worlds/'], shell=True)
                await ctx.send(world + '\nImported successfully!')
                await ctx.send('Use !selectworld \"' + world + '\" to select it.')
        else:
            await ctx.send('File was not a zip archive :-(')
    except:
        await ctx.send('Unable to download file from url :-(')
        pass
    subprocess.run(['rm', '-rf', SCRIPTS_PATH + 'blorgle'])


bot.run(TOKEN)
