import asyncio
import threading
import os
import time
from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    print("Connected guilds:", bot.guilds)

@bot.command()
async def announce(ctx, *, message: str):
    await ctx.send(message)

@app.route('/')
def home():
    return render_template_string('''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>MYYOOMI Discord Bot Announcer</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <script>
                async function fetchGuilds() {
                    let response = await fetch('/guilds');
                    let guilds = await response.json();
                    let select = document.getElementById('guildSelect');
                    select.innerHTML = '<option value="">Select a server</option>';
                    guilds.forEach(guild => {
                        let option = document.createElement('option');
                        option.value = guild.id;
                        option.textContent = guild.name;
                        select.appendChild(option);
                    });
                }
                async function fetchChannelsAndMembers() {
                    let guildId = document.getElementById('guildSelect').value;
                    if (!guildId) return;
                    
                    let channelResponse = await fetch(`/channels?guild_id=${guildId}`);
                    let channels = await channelResponse.json();
                    let channelContainer = document.getElementById('channelsContainer');
                    channelContainer.innerHTML = '';
                    channels.forEach(channel => {
                        let div = document.createElement('div');
                        div.classList.add('form-check');
                        div.innerHTML = `<input class="form-check-input" type="checkbox" name="channels" value="${channel.id}"> ${channel.name}`;
                        channelContainer.appendChild(div);
                    });
                    
                    let memberResponse = await fetch(`/members?guild_id=${guildId}`);
                    let members = await memberResponse.json();
                    let memberContainer = document.getElementById('membersContainer');
                    memberContainer.innerHTML = '';
                    members.forEach(member => {
                        let div = document.createElement('div');
                        div.classList.add('form-check');
                        div.innerHTML = `<input class="form-check-input" type="checkbox" name="members" value="${member.id}"> ${member.name}`;
                        memberContainer.appendChild(div);
                    });
                }
            </script>
        </head>
        <body class="text-white bg-dark" onload="fetchGuilds()">
            <div class="container mt-5">
                <div class="text-white bg-dark card shadow p-4">
                    <h1 class="text-center">MYYOOMI Discord Bot Announcer</h1>
                    <form class="text-white bg-dark" action="/announce" method="post">
                        <div class="mb-3">
                            <label class="form-label">Select Server</label>
                            <select class="form-control" id="guildSelect" name="guild_id" onchange="fetchChannelsAndMembers()" required></select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Select Channels</label>
                            <div id="channelsContainer"></div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Select Members to Tag</label>
                            <div id="membersContainer"></div>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Title</label>
                            <input type="text" class="form-control" name="title" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Message</label>
                            <textarea class="form-control" name="message" rows="4" required></textarea>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Image URL</label>
                            <input type="text" class="form-control" name="image_url">
                        </div>
                        <div class="mb-3">
                            <label class="form-label">Tag Everyone</label>
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" name="tag_everyone" value="yes">
                                <label class="form-check-label">Yes, tag @everyone</label>
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Send Announcement</button>
                    </form>
                </div>
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
    ''')

@app.route('/guilds')
def get_guilds():
    guilds = [{'id': str(g.id), 'name': g.name} for g in bot.guilds]
    return jsonify(guilds)

@app.route('/channels')
def get_channels():
    guild_id = request.args.get('guild_id', type=int)
    guild = bot.get_guild(guild_id)
    if not guild:
        return jsonify([])
    channels = [{'id': str(c.id), 'name': c.name} for c in guild.text_channels]
    return jsonify(channels)

@app.route('/members')
def get_members():
    guild_id = request.args.get('guild_id', type=int)
    guild = bot.get_guild(guild_id)
    if not guild:
        return jsonify([])
    members = [{'id': str(m.id), 'name': m.display_name} for m in guild.members if not m.bot]
    return jsonify(members)

@app.route('/announce', methods=['POST'])
def announce_web():
    guild_id = int(request.form.get('guild_id'))
    channel_ids = request.form.getlist('channels')
    member_ids = request.form.getlist('members')
    title = request.form.get('title')
    message = request.form.get('message').replace("\r\n", "\n")
    image_url = request.form.get('image_url', '').strip()
    tag_everyone = request.form.get('tag_everyone') == "yes"

    member_mentions = ' '.join([f'<@{mid}>' for mid in member_ids])
    everyone_mention = "@everyone" if tag_everyone else ""

    async def send_message():
        guild = bot.get_guild(guild_id)
        if guild:
            for channel_id in channel_ids:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    content = f'**{title}**\n{message}\n{everyone_mention} {member_mentions}'.strip()
                    await channel.send(content)
                    if image_url:
                        await channel.send(image_url)

    asyncio.run_coroutine_threadsafe(send_message(), bot.loop)
    return redirect(url_for('home'))

if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5709, 'debug': False}, daemon=True).start()
    time.sleep(5)
    asyncio.run(bot.start(os.getenv("DISCORD_BOT_TOKEN")))