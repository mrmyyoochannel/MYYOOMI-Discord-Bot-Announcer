import asyncio
import threading
import os
import time
import uuid
from flask import Flask, request, render_template_string, redirect, url_for, jsonify, session
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask_cors import CORS
from datetime import datetime, timedelta
from functools import wraps

# โหลด .env
load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "devkey")

LOGIN_USER = os.getenv("LOGIN_USER", "admin")
LOGIN_PASSWORD = os.getenv("LOGIN_PASSWORD", "password")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login_page', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# ---------- Discord Bot Setup ----------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))
WELCOME_MESSAGE = os.getenv("WELCOME_MESSAGE", "ยินดีต้อนรับ {mention} เข้าสู่ {guild}!")

VOTE_SESSIONS = {}

def generate_vote_id():
    return str(uuid.uuid4())[:8]

# ---------- Discord Events ----------
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    print(f"{member} : joined")
    if channel:
        message = WELCOME_MESSAGE.format(mention=member.mention, guild=member.guild.name)
        embed = discord.Embed(
            title="🎉 ยินดีต้อนรับ!",
            description=message,
            color=0x00ff00
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_image(url="https://sv1.img.in.th/7inf7D.gif")
        embed.set_footer(text=f"สมาชิกใหม่: {member.name}")
        await channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    print(f"{member} : Leave")
    if channel:
        embed = discord.Embed(
            title="👋 สมาชิกออกจากเซิร์ฟเวอร์",
            description=f'{member.mention} ได้ออกจากเซิร์ฟเวอร์ {member.guild.name}',
            color=0xff0000
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
        embed.set_footer(text=f"สมาชิกที่ออก: {member.name}")
        await channel.send(embed=embed)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    print("Connected guilds:", [g.name for g in bot.guilds])

@bot.command()
async def announce(ctx, *, message: str):
    await ctx.send(message)

@bot.event
async def on_raw_reaction_add(payload):
    for vote_id, vote in VOTE_SESSIONS.items():
        if vote.get('message_id') == payload.message_id and datetime.utcnow() < vote['end_time']:
            try:
                idx = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'].index(str(payload.emoji))
            except ValueError:
                return
            if not payload.member or payload.member.bot:
                return
            vote['votes'][payload.user_id] = idx

@bot.event
async def on_raw_reaction_remove(payload):
    for vote_id, vote in VOTE_SESSIONS.items():
        if vote.get('message_id') == payload.message_id and datetime.utcnow() < vote['end_time']:
            try:
                idx = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟'].index(str(payload.emoji))
            except ValueError:
                return
            if payload.user_id in vote['votes'] and vote['votes'][payload.user_id] == idx:
                del vote['votes'][payload.user_id]

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    error = ""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == LOGIN_USER and password == LOGIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('home'))
        else:
            error = "ชื่อผู้ใช้หรือรหัสผ่านผิด"
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>เข้าสู่ระบบ - MutodGrob</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5">
            <div class="card bg-dark text-white p-4 shadow col-md-6 offset-md-3">
                <h1 class="text-center mb-4">🔐 เข้าสู่ระบบ</h1>
                <form method="post">
                    <div class="mb-3">
                        <label>ชื่อผู้ใช้</label>
                        <input type="text" class="form-control" name="username" required autofocus>
                    </div>
                    <div class="mb-3">
                        <label>รหัสผ่าน</label>
                        <input type="password" class="form-control" name="password" required>
                    </div>
                    {% if error %}
                    <div class="alert alert-danger">{{ error }}</div>
                    {% endif %}
                    <button type="submit" class="btn btn-primary w-100">เข้าสู่ระบบ</button>
                </form>
            </div>
        </div>
    </body>
    </html>
    ''', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login_page'))

# ---------- Web Control Panel (protected) ----------
@app.route('/')
@login_required
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>MutodGrob - หน้าหลัก</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5 text-center">
         <div class="text-center">
            <img src="https://sv1.img.in.th/7iazJC.jpeg" class="img-fluid rounded-circle mx-auto d-block" alt="logo" style="max-width: 200px; height: auto;">
        </div>
            <h1 class="mb-4">🤖 MutodGrob Bot Control Panel</h1>
            <div class="d-grid gap-3 col-6 mx-auto">
                <a href="/settings" class="btn btn-warning btn-lg">⚙️ ตั้งค่า </a>
                <a href="/announcements" class="btn btn-success btn-lg">📢 ส่งประกาศ</a>
                <a href="/vote" class="btn btn-primary btn-lg">🗳️ สร้าง/ดูโหวต</a>
                <a href="/help" class="btn btn-info btn-lg">❓ วิธีใช้งาน</a>
                <a href="/logout" class="btn btn-danger btn-lg">ออกจากระบบ</a>
            </div>
            <p class="mt-3 text-danger">❗ถ้ากดส่งข้อมูลไปแล้ว หรือ ระบบไม่ทำงาน รบกวนแจ้ง เพื่อทำการแก้ไข</p>
            <p class="mt-3 text-danger">❗ระบบอยู่ในช่วง พัฒนา อาจะมี บัคหรือ ปัญหาได้</p>
            <p class="mt-3">สร้าง และ แก้ไขโดย: <a href="https://myyoomi.carrd.co/" class="text-info">™MYYOOMI</a></p>
        </div>
    </body>
    </html>
    ''')

@app.route('/settings')
@login_required
def settings():
    return render_template_string(open("settings.html", encoding="utf-8").read())

@app.route('/announcements')
@login_required
def announcement_page():
    return render_template_string(open("announcements.html", encoding="utf-8").read())

@app.route('/help')
@login_required
def help_page():
    return render_template_string(open("help.html", encoding="utf-8").read())

@app.route('/vote', methods=['GET', 'POST'])
@login_required
def vote_page():
    if request.method == 'POST':
        vote_title = request.form.get('title')
        options = [o.strip() for o in request.form.get('options', '').split('\n') if o.strip()]
        channel_id = int(request.form.get('channel_id'))
        guild_id = int(request.form.get('guild_id'))
        duration_min = int(request.form.get('duration', 5))
        end_time = datetime.utcnow() + timedelta(minutes=duration_min)
        vote_id = generate_vote_id()
        VOTE_SESSIONS[vote_id] = {
            'title': vote_title,
            'options': options,
            'message_id': None,
            'channel_id': channel_id,
            'guild_id': guild_id,
            'end_time': end_time,
            'votes': {},
        }
        async def send_vote():
            channel = bot.get_channel(channel_id)
            emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
            description = ''
            for idx, opt in enumerate(options):
                description += f"{emojis[idx]} {opt}\n"
            embed = discord.Embed(
                title=f'🗳️ โหวต: {vote_title}',
                description=description + f"\nโหวตสิ้นสุด <t:{int(end_time.timestamp())}:R>",
                color=0x3498db
            )
            embed.set_footer(text=f'Vote ID: {vote_id}')
            msg = await channel.send(embed=embed)
            VOTE_SESSIONS[vote_id]['message_id'] = msg.id
            for i in range(len(options)):
                await msg.add_reaction(emojis[i])
        asyncio.run_coroutine_threadsafe(send_vote(), bot.loop)
        return redirect(url_for('vote_page'))
    return render_template_string(open("vote.html", encoding="utf-8").read())

@app.route('/vote/list')
@login_required
def vote_list_api():
    now = datetime.utcnow()
    votes = []
    for vid, v in VOTE_SESSIONS.items():
        if v['end_time'] > now:
            votes.append({
                'vote_id': vid,
                'title': v['title'],
                'remaining': str(v['end_time'] - now).split('.')[0]
            })
    return jsonify(votes)

@app.route('/vote/result/<vote_id>')
@login_required
def vote_result_page(vote_id):
    vote = VOTE_SESSIONS.get(vote_id)
    if not vote:
        return "Vote ID not found", 404
    count = [0] * len(vote['options'])
    for user_id, idx in vote['votes'].items():
        if 0 <= idx < len(count):
            count[idx] += 1
    total = sum(count)
    result_html = ""
    emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    for idx, opt in enumerate(vote['options']):
        percent = (count[idx] / total * 100) if total else 0
        result_html += f"<b>{emojis[idx]} {opt}</b>: {count[idx]} เสียง ({percent:.1f}%)<br>"
    ended = datetime.utcnow() > vote['end_time']
    return f'''
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>📊 ผลโหวต - {vote["title"]}</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5">
            <div class="card bg-dark text-white p-4 shadow">
                <h2 class="text-center">📊 ผลโหวต</h2>
                <h3 class="text-center">{vote["title"]}</h3>
                <div class="mt-3">
                    {result_html}
                </div>
                <div class="mt-3 text-info">Vote ID: <b>{vote_id}</b></div>
                <div class="mt-3 text-danger">{'⏰ หมดเวลาลงคะแนน' if ended else '⏰ ยังเปิดรับคะแนน'}</div>
                <a href="/vote" class="btn btn-secondary w-100 mt-3">⬅️ กลับหน้าโหวต</a>
            </div>
        </div>
    </body>
    </html>
    '''

# ---------- API ไม่ต้องล็อกอิน (สำหรับ JS) ----------
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
@login_required
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

@app.route('/set_welcome_channel', methods=['POST'])
@login_required
def set_welcome_channel():
    global WELCOME_CHANNEL_ID
    data = request.json
    new_channel_id = int(data.get("channel_id", 0))
    WELCOME_CHANNEL_ID = new_channel_id
    os.environ["WELCOME_CHANNEL_ID"] = str(new_channel_id)
    return jsonify({"message": "Welcome channel updated!", "channel_id": new_channel_id})

@app.route('/set_welcome_message', methods=['POST'])
@login_required
def set_welcome_message():
    global WELCOME_MESSAGE
    data = request.json
    new_message = data.get("message", "")
    WELCOME_MESSAGE = new_message
    os.environ["WELCOME_MESSAGE"] = new_message  
    return jsonify({"message": "Welcome message updated!", "content": new_message})

@app.route('/set_status', methods=['POST'])
@login_required
def set_status():
    data = request.json
    status_text = data.get("status", "กำลังรับข้อมูล...")
    async def update_status():
        await bot.change_presence(activity=discord.Game(name=status_text))
    asyncio.run_coroutine_threadsafe(update_status(), bot.loop)
    return jsonify({"message": "Status updated!"})

if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 5709, 'debug': False}, daemon=True).start()
    time.sleep(5)
    asyncio.run(bot.start(os.getenv("DISCORD_BOT_TOKEN")))
