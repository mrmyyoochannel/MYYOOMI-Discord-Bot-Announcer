# Discord-Bot-Announcer
#Ver.Thai: 2.0
#Ver.ENG: 1.6

Discord Bot Announcer in Python. This project uses Bootstrap.

## Setup
1. **Install Flask:**
   - Create a virtual environment and activate it:
     ```sh
     python -m venv venv
     source venv/bin/activate  # Use .\venv\Scripts\activate for Windows
     ```
   - Install Flask within the virtual environment:
     ```sh
     pip install Flask
     pip install discord.py
     pip install python-dotenv
     pip install watchdog
     pip install flask-cors
     ```

2. **Configure Environment Variables:**
   - Open the `.env` file. If it doesn't exist, you can create it.
   - Add your Discord bot token:
     ``` 
     DISCORD_BOT_TOKEN=<your_token_here>
     WELCOME_CHANNEL_ID=<your_WELCOME_CHANNEL_ID>
     LOGIN_USER=<your_USER>
     LOGIN_PASSWORD=<your_PASSWORD>
     FLASK_SECRET_KEY=<your_SECRET_KEY>
     ```

3. **Set Up Server:**
   - The bot runs on `0.0.0.0` at port `5709` by default.
   - You can edit the port in the `app.py` file (line 176).
   - **Note:** This project requires Python version 12 or higher.

## Starting the Bot

```bash
python app.py

```

I hope this helps! If there's anything more you need, feel free to let me know.
