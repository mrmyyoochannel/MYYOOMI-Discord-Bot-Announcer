import asyncio
import threading
import os
import time
from flask import Flask, request, render_template_string, redirect, url_for, jsonify
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))

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
        embed.set_image(url="https://yourpicture.png")
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

@app.route('/set_welcome_channel', methods=['POST'])
def set_welcome_channel():
    global WELCOME_CHANNEL_ID
    data = request.json
    new_channel_id = int(data.get("channel_id", 0))
    WELCOME_CHANNEL_ID = new_channel_id
    os.environ["WELCOME_CHANNEL_ID"] = str(new_channel_id)
    return jsonify({"message": "Welcome channel updated!", "channel_id": new_channel_id})

@app.route('/set_welcome_message', methods=['POST'])
def set_welcome_message():
    global WELCOME_MESSAGE
    data = request.json
    new_message = data.get("message", "")
    WELCOME_MESSAGE = new_message
    os.environ["WELCOME_MESSAGE"] = new_message  
    return jsonify({"message": "Welcome message updated!", "content": new_message})


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    print("Connected guilds:", [g.name for g in bot.guilds])

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
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>หน้าหลัก</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5 text-center">
         <div class="text-center">
            <img src="https://yourpicture.png" class="img-fluid rounded-circle mx-auto d-block" alt="logo" style="max-width: 200px; height: auto;">
        </div>
            <h1 class="mb-4">🤖 MutodGrob Bot Control Panel</h1>
            <div class="d-grid gap-3 col-6 mx-auto">
                <a href="/settings" class="btn btn-warning btn-lg">⚙️ ตั้งค่า </a>
                <a href="/announcements" class="btn btn-success btn-lg">📢 ส่งประกาศ</a>
                <a href="/help" class="btn btn-info btn-lg">❓ วิธีใช้งาน</a>
            </div>
            <p class="mt-3 text-danger">❗ถ้ากดส่งข้อมูลไปแล้ว หรือ ระบบไม่ทำงาน รบกวนแจ้ง เพื่อทำการแก้ไข</p>
            <p class="mt-3 text-danger">❗ระบบอยู่ในช่วง พัฒนา อาจะมี บัคหรือ ปัญหาได้</p>
            <p class="mt-3">สร้าง และ แก้ไขโดย: <a href="https://myyoomi.carrd.co/" class="text-info">™MYYOOMI</a></p>
        </div>
    </body>
    </html>
    ''')

@app.route('/settings')
def settings():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Bot Controls - MutodGrob</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
    </head>
    <body class="text-white bg-dark">
        <div class="container mt-5">
            <div class="card bg-dark text-white p-4 shadow">
                  <div class="text-center">
                    <img src="https://yourpicture.png" class="img-fluid rounded-circle mx-auto d-block" alt="logo" style="max-width: 200px; height: auto;">
                </div>
                <h1 class="text-center mb-4">⚙️ ตั้งค่าบอท </h1>
                <button class="btn btn-info w-100 mb-3" onclick="updateStatus()">🔄 อัปเดตสถานะบอท</button>
                <button class="btn btn-info w-100 mb-3" onclick="updateWelcomeChannel()">🗨️ ตั้งค่าห้องต้อนรับ</button>
                <button class="btn btn-info w-100 mb-3" onclick="updateWelcomeMessage()">📝 ตั้งค่าข้อความต้อนรับ</button>
                <a href="/" class="btn btn-secondary w-100 mt-3">⬅️ กลับหน้าแรก</a>
            </div>
            <p class="mt-3 text-danger">❗ถ้ากดส่งข้อมูลไปแล้ว หรือ ระบบไม่ทำงาน รบกวนแจ้ง เพื่อทำการแก้ไข</p>
            <p class="mt-3">สร้าง และ แก้ไขโดย: <a href="https://myyoomi.carrd.co/" class="text-info">™MYYOOMI</a></p>
        </div>

        <script>
            async function updateWelcomeMessage() {
                const { value: welcomeMsg } = await Swal.fire({
                    title: 'ตั้งค่าข้อความต้อนรับ',
                    input: 'textarea',
                    inputLabel: 'คุณสามารถใช้ {mention} สำหรับแท็กผู้ใช้ และ {guild} สำหรับชื่อเซิร์ฟเวอร์',
                    inputPlaceholder: 'ยินดีต้อนรับ {mention} เข้าสู่ {guild}!',
                    showCancelButton: true,
                    inputValidator: (value) => {
                        if (!value) return 'กรุณาใส่ข้อความต้อนรับ';
                    }
                });

                if (welcomeMsg) {
                    await fetch('/set_welcome_message', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: welcomeMsg })
                    });
                    Swal.fire('สำเร็จ!', 'ข้อความต้อนรับได้รับการอัปเดตแล้ว', 'success');
                }
            }

            async function updateStatus() {
                const { value: newStatus } = await Swal.fire({
                    title: 'อัปเดต สถานะ',
                    input: 'text',
                    inputLabel: 'ใส่สถานะให้บอทแสดง:',
                    showCancelButton: true,
                    inputValidator: (value) => {
                        if (!value) {
                            return 'คุณต้องเขียนอะไรซักอย่าง!'
                        }
                    }
                });

                if (newStatus) {
                    await fetch('/set_status', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({status: newStatus})
                    });
                    Swal.fire('อัปเดตสำเร็จ!', 'บอทได้เปลี่ยนสถานะแล้ว', 'success');
                }
            }

            async function updateWelcomeChannel() {
                const { value: channelId } = await Swal.fire({
                    title: 'Set Welcome Channel',
                    input: 'text',
                    inputLabel: 'ใส่ ID ห้องที่ต้องการให้บอทแจ้งเตือนคนเข้า:',
                    showCancelButton: true,
                    inputValidator: (value) => {
                        if (!value) {
                            return 'คุณต้องเขียนอะไรซักอย่าง!'
                        }
                    }
                });

                if (channelId) {
                    await fetch('/set_welcome_channel', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({channel_id: channelId})
                    });
                    Swal.fire('ตั้งค่าสำเร็จ!', 'ห้องต้อนรับถูกตั้งค่าแล้ว', 'success');
                }
            }
        </script>
    </body>
    
    </html>
    ''')
    
@app.route('/announcements')
def announcement_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>📢 ระบบประกาศ - MutodGrob</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5">
            <div class="card bg-dark text-white p-4 shadow">
                <div class="text-center">
                    <img src="https://yourpicture.png" class="img-fluid rounded-circle mx-auto d-block" alt="logo" style="max-width: 200px; height: auto;">
                </div>
                <h1 class="text-center mb-4">📢 ระบบประกาศข้อความ 📢</h1>
                <form action="/announce" method="post" onsubmit="handleSubmit(event)">
                    <div class="mb-3">
                        <label>🌐 เลือกเซิร์ฟเวอร์</label>
                        <p class="mt-3 text-danger">❗ถ้าข้อมูลไม่โหลด หรือ ไม่เจอเซิฟเวอร์ ให้ รีโหลด หน้าเว็บไหม่</p>
                        <select class="form-control" id="guildSelect" name="guild_id" onchange="fetchChannelsAndMembers()" required></select>
                    </div>
                    <div class="mb-3">
                        <label>📁 เลือกช่อง</label>
                        <div id="channelsContainer"></div>
                    </div>
                    <div class="mb-3">
                        <label>👥 เลือกสมาชิก</label>
                        <p class="mt-3 text-danger">❗เลือกได้หลายตัวเลือก</p>
                        <div id="membersContainer"></div>
                    </div>
                    <div class="mb-3">
                        <label>✏️ ชื่อเรื่อง</label>
                        <p class="mt-3 text-danger">❗สามารถ ส่งอิโมจิ/ตัวอักศรพิเศษ ได้</p>
                        <input type="text" class="form-control" name="title" required>
                    </div>
                    <div class="mb-3">
                        <label>📄 ข้อความ</label>
                        <p class="mt-3 text-danger">❗สามารถ ส่งแบบเว้นบรรนทัดได้ ส่งอิโมจิ/ตัวอักศรพิเศษ ได้</p>
                        <textarea class="form-control" name="message" rows="4" required></textarea>
                    </div>
                    <div class="mb-3">
                        <label>🖼️ URL รูปภาพ (ถ้ามี)</label>
                        <input type="text" class="form-control" name="image_url">
                    </div>
                    <div class="form-check mb-2">
                        <input class="form-check-input" type="checkbox" name="tag_everyone" value="yes">
                        <label class="form-check-label">แท็ก @everyone</label>
                    </div>
                    <div class="form-check mb-3">
                        <input class="form-check-input" type="checkbox" name="send_as_embed" id="embedCheck" value="yes" onchange="toggleColorPicker()">
                        <label class="form-check-label">ส่งเป็น Embed</label>
                    </div>
                    <div class="mb-3" id="colorPicker" style="display: none;">
                        <label>เลือกสี Embed</label>
                        <input type="color" class="form-control" name="color" value="#00ff00">
                    </div>
                    <button type="submit" class="btn btn-success w-100">🚀 ส่งประกาศ</button>
                </form>
                <a href="/" class="btn btn-secondary w-100 mt-3">⬅️ กลับหน้าหลัก</a>
            </div>
            <p class="mt-3 text-danger">❗ถ้ากดส่งข้อมูลไปแล้ว หรือ ระบบไม่ทำงาน รบกวนแจ้ง เพื่อทำการแก้ไข</p>
            <p class="mt-3">สร้าง และ แก้ไขโดย: <a href="https://myyoomi.carrd.co/" class="text-info">™MYYOOMI</a></p>
        </div>

        <script>
        async function fetchGuilds() {
            let response = await fetch('/guilds');
            let guilds = await response.json();
            let select = document.getElementById('guildSelect');
            select.innerHTML = '<option value="">เลือกเซิร์ฟเวอร์</option>';
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

            let channels = await (await fetch(`/channels?guild_id=${guildId}`)).json();
            let members = await (await fetch(`/members?guild_id=${guildId}`)).json();

            let channelContainer = document.getElementById('channelsContainer');
            let memberContainer = document.getElementById('membersContainer');

            channelContainer.innerHTML = '';
            channels.forEach(c => {
                channelContainer.innerHTML += `<div class="form-check"><input class="form-check-input" type="checkbox" name="channels" value="${c.id}"> ${c.name}</div>`;
            });

            memberContainer.innerHTML = '';
            members.forEach(m => {
                memberContainer.innerHTML += `<div class="form-check"><input class="form-check-input" type="checkbox" name="members" value="${m.id}"> ${m.name}</div>`;
            });
        }
        function toggleColorPicker() {
            const embedCheck = document.getElementById('embedCheck');
            const colorPicker = document.getElementById('colorPicker');
            colorPicker.style.display = embedCheck.checked ? 'block' : 'none';
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
                Swal.fire('สำเร็จ!', 'ประกาศถูกส่งแล้ว', 'success');
            } else {
                Swal.fire('ผิดพลาด!', 'ไม่สามารถส่งประกาศได้', 'error');
            }
        }
        window.onload = function() {
            fetchGuilds();
            toggleColorPicker();
        }
        </script>
    </body>
    </html>
    ''')

@app.route('/help')
def help_page():
    return render_template_string('''
    <!DOCTYPE html>
    <html lang="th">
    <head>
        <meta charset="UTF-8">
        <title>📘 วิธีใช้งาน - MutodGrob</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body class="bg-dark text-white">
        <div class="container mt-5">
            <div class="text-center mb-4">
                <img src="https://yourpicture.png" class="img-fluid rounded-circle" style="max-width: 150px;" alt="logo">
                <h1 class="mt-3">❓ วิธีใช้งานระบบ MutodGrob</h1>
            </div>
            <div class="card bg-secondary p-4 text-start">
                <h4>⚙️ หน้า ตั้งค่า</h4>
                <ul>
                    <li><strong>📝 ตั้งค่าข้อความต้อนรับ:</strong> ใส่ข้อความที่จะใช้ต้อนรับสมาชิกใหม่ เช่น <code>ยินดีต้อนรับ {mention} เข้าสู่ {guild}</code></li>
                    <li><strong>🗨️ ตั้งค่าห้องต้อนรับ:</strong> กรอก ID ห้อง Discord ที่จะใช้ส่งข้อความต้อนรับ</li>
                    <li><strong>🔄 อัปเดตสถานะ:</strong> เปลี่ยนข้อความสถานะของบอท</li>
                </ul>

                <h4 class="mt-4">📢 หน้า ประกาศ</h4>
                <ul>
                    <li>เลือกเซิร์ฟเวอร์ และห้องที่ต้องการส่ง</li>
                    <li>เลือกสมาชิกที่ต้องการแท็ก (เลือกหลายคนได้)</li>
                    <li>กรอกชื่อเรื่อง และข้อความประกาศ</li>
                    <li>แนบรูปภาพได้ (ใส่ URL เท่านั้น)</li>
                    <li>เลือกส่งแบบ Embed ได้ พร้อมกำหนดสี</li>
                    <li>สามารถแท็ก @everyone ได้</li>
                </ul>

                <h4 class="mt-4">🛠️ หมายเหตุ</h4>
                <ul>
                    <li>ถ้าระบบไม่ทำงาน ให้รีเฟรชหรือติดต่อผู้ดูแล</li>
                    <li>ระบบยังอยู่ในช่วงพัฒนา อาจมีบัคหรือปัญหา</li>
                </ul>
            </div>
            <div class="text-center mt-4">
                <a href="/" class="btn btn-light">⬅️ กลับหน้าหลัก</a>
                <p class="mt-3">สร้าง และ แก้ไขโดย: <a href="https://myyoomi.carrd.co/" class="text-info">™MYYOOMI</a></p>
            </div>
        </div>
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