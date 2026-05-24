import os
import requests
import pandas as pd
from pyrogram import Client, filters
import re
import yt_dlp

API_ID = 36864805
API_HASH = "718a522975ce10d04f583eaf5fa7b78e"
BOT_TOKEN = "8883342244:AAHR3Qn5IfFKDRJWKHgN5I-8sHXKAF9XoPM"

app = Client("cloud_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
user_states = {}
user_channels = {}

def clean_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", str(name).strip())
    return name + '.mp4' if not name.lower().endswith('.mp4') else name

@app.on_message(filters.command("start") & filters.private)
async def start(client, message):
    user_states[message.chat.id] = "CHANNEL"
    await message.reply_text("🤖 Bot Started! Kripya Target Channel ka Username bhejein (jaise @mychannel):")

@app.on_message(filters.text & filters.private & ~filters.command("start"))
async def set_channel(client, message):
    if user_states.get(message.chat.id) == "CHANNEL":
        user_channels[message.chat.id] = message.text.strip()
        user_states[message.chat.id] = "FILE"
        await message.reply_text(f"✅ Channel set to {message.text}.\n📁 Ab apni Excel (.xlsx) ya CSV file bhejein.")

@app.on_message(filters.document & filters.private)
async def process_file(client, message):
    if user_states.get(message.chat.id) != "FILE":
        return await message.reply_text("⚠️ Pehle /start dabayein.")
    
    target_channel = user_channels[message.chat.id]
    msg = await message.reply_text("📥 File receive ho gayi. Reading data...")
    file_path = await message.download()
    
    try:
        df = pd.read_csv(file_path, header=None) if file_path.endswith('.csv') else pd.read_excel(file_path, header=None)
        df = df.dropna(how='all')
    except Exception as e:
        os.remove(file_path)
        return await msg.edit_text(f"❌ File Error: {e}")
    
    await msg.edit_text(f"✅ Total {len(df)} videos mili. Downloading start kar raha hu.\n\n💻 **AB AAP LAPTOP BAND KAR SAKTE HAIN!**")
    
    for index, row in df.iterrows():
        try:
            raw_name, v_link = (row.iloc[1], str(row.iloc[2]).strip()) if len(df.columns) >= 3 else (row.iloc[0], str(row.iloc[1]).strip())
            if pd.isna(raw_name) or 'http' not in v_link: continue
            
            v_name = clean_filename(raw_name)
            await message.reply_text(f"⏳ Downloading: {v_name}")
            
            if '.m3u8' in v_link:
                ydl_opts = {'outtmpl': v_name, 'format': 'best', 'quiet': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl: ydl.download([v_link])
            else:
                res = requests.get(v_link, stream=True, timeout=30)
                with open(v_name, 'wb') as f:
                    for chunk in res.iter_content(chunk_size=1024*1024*5):
                        if chunk: f.write(chunk)
                        
            await app.send_video(chat_id=target_channel, video=v_name, caption=f"🎬 {v_name.replace('.mp4', '')}", supports_streaming=True)
            os.remove(v_name)
        except Exception as e:
            await message.reply_text(f"❌ Error in {v_name}: {e}")
            if os.path.exists(v_name): os.remove(v_name)
        
    os.remove(file_path)
    user_states[message.chat.id] = None
    await message.reply_text("🎉=== BATCH SUCCESSFULLY UPLOAD HO GAYA ===🎉\nNaya batch daalne ke liye /start karein.")

app.run()
