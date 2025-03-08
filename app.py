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

@app.route('/set_status', methods=['POST'])
def set_status():
    data = request.json
    status_text = data.get("status", "กำลังรับข้อมูล...")
    
    async def update_status():
        await bot.change_presence(activity=discord.Game(name=status_text))
    
    asyncio.run_coroutine_threadsafe(update_status(), bot.loop)
    return jsonify({"message": "Status updated!"})

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Announcement Bot by MYYOOMI</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    <script>
        async function fetchGuilds() {
            let response = await fetch('/guilds');
            let guilds = await response.json();
            let select = document.getElementById('guildSelect');
            select.innerHTML = '<option value="">Select Server</option>';
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
        
        function toggleColorPicker() {
            const embedCheck = document.getElementById('embedCheck');
            const colorPicker = document.getElementById('colorPicker');
            colorPicker.style.display = embedCheck.checked ? 'block' : 'none';
        }
        async function updateStatus() {
            const { value: newStatus } = await Swal.fire({
                title: 'Update Status',
                input: 'text',
                inputLabel: 'Enter new status',
                showCancelButton: true,
                inputValidator: (value) => {
                    if (!value) {
                        return 'You need to write something!'
                    }
                }
            });

            if (newStatus) {
                await fetch('/set_status', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({status: newStatus})
                });
                Swal.fire({
                    title: 'Status Updated!',
                    text: 'The status has been successfully updated.',
                    icon: 'success',
                    confirmButtonText: 'OK'
                });
            }
        }
        async function handleSubmit(event) {
            event.preventDefault();
            let form = event.target;
            let formData = new FormData(form);
            let response = await fetch(form.action, {
                method: 'POST',
                body: formData
            });
            if (response.ok) {
                Swal.fire({
                    title: 'Success!',
                    text: 'Your announcement has been sent.',
                    icon: 'success',
                    confirmButtonText: 'OK'
                });
            } else {
                Swal.fire({
                    title: 'Error!',
                    text: 'There was a problem sending your announcement.',
                    icon: 'error',
                    confirmButtonText: 'OK'
                });
            }
        }
    </script>
</head>
<body class="text-white bg-dark" onload="fetchGuilds(); toggleColorPicker();">
    <div class="container mt-5">
        <div class="text-white bg-dark card shadow p-4">
            <div class="text-center">
                <img src="" class="rounded-circle" alt="logo">
            </div>
            <h1 class="text-center">⚒️Control Panel Announcement Bot⚒️</h1>
            <form class="text-white bg-dark" action="/announce" method="post" onsubmit="handleSubmit(event)">
                <div class="mb-3">
                    <label class="form-label">🌐Select Server</label>
                    <select class="form-control" id="guildSelect" name="guild_id" onchange="fetchChannelsAndMembers()" required></select>
                </div>
                <div class="mb-3">
                    <label class="form-label">📁Select Channel (Only one channel can be selected, the bot must have permission to send messages)</label>
                    <div id="channelsContainer"></div>
                </div>
                <div class="mb-3">
                    <label class="form-label">👥Select Members to Tag (Multiple options can be selected)</label>
                    <div id="membersContainer"></div>
                </div>
                <div class="mb-3">
                    <label class="form-label">✏️Title/Headline (Can include - or numbers, special characters, and emojis)</label>
                    <input type="text" class="form-control" name="title" required>
                </div>
                <div class="mb-3">
                    <label class="form-label">✏️Message (Can be sent as multiple lines, can include - or numbers, special characters, and emojis)</label>
                    <textarea class="form-control" name="message" rows="4" required></textarea>
                </div>
                <div class="mb-3">
                    <label class="form-label">🖼️Image URL</label>
                    <input type="text" class="form-control" name="image_url">
                </div>
                <div class="mb-3">
                    <label class="form-label">Tag everyone❓</label>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" name="tag_everyone" value="yes">
                        <label class="form-check-label">✅Yes, tag @everyone</label>
                    </div>
                </div>
                <div class="mb-3">
                    <label class="form-label">Send as embed❓</label>
                    <div class="form-check">
                        <input class="form-check-input" type="checkbox" name="send_as_embed" id="embedCheck" value="yes" onchange="toggleColorPicker()">
                        <label class="form-check-label">✅Yes, send as announcement</label>
                    </div>
                </div>
                <div class="mb-3" id="colorPicker" style="display: none;">
                    <label class="form-label">🖌️Choose Color</label>
                    <input type="color" class="form-control" name="color" value="#00ff00">
                </div>
                <button type="submit" class="btn btn-primary w-100">📨 Send Announcement 📨</button>
            </form>
            <div class="mb-3">
                <button class="btn btn-info w-100 mt-3" onclick="updateStatus()">🔄Update Status</button>
            </div>
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
    send_as_embed = request.form.get('send_as_embed') == "yes"
    color = request.form.get('color', '#00ff00').lstrip('#')
    color = int(color, 16)

    member_mentions = ' '.join([f'<@{mid}>' for mid in member_ids])
    everyone_mention = "@everyone" if tag_everyone else ""

    async def send_message():
        guild = bot.get_guild(guild_id)
        if guild:
            for channel_id in channel_ids:
                channel = bot.get_channel(int(channel_id))
                if channel:
                    if send_as_embed:
                        embed = discord.Embed(title=title, description=message, color=color)
                        if image_url:
                            embed.set_image(url=image_url)
                        if tag_everyone or member_mentions:
                            embed.add_field(name="Mentions", value=f'{everyone_mention} {member_mentions}', inline=False)
                        await channel.send(embed=embed)
                    else:
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
