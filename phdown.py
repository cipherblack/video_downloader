import os
import validators
from datetime import datetime
from pyrogram import Client, filters ,errors
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Message, CallbackQuery, ReplyKeyboardMarkup
from pyrogram.errors import exceptions
import sqlite3
import pyromod
import asyncio
import json
from tqdm.asyncio import tqdm
conn = sqlite3.connect("video_dl.db")
cursor = conn.cursor()

# Create users table if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        last_download DATE,
        downloads_count INTEGER DEFAULT 0,
        video_limit INTEGER DEFAULT 4,
        size_limit INTEGER DEFAULT 52428800,
        disable BOOLEAN DEFAULT FALSE
    )
""")

conn.commit()

bot = Client(
    name="video_dl",
    api_id=1234567, # api id 
    api_hash="api_hash", # api hash,
    bot_token="BOT_TOkEN" # bot token  
)
OWNER = 123456 # userid for owner
ADMIN_USER_IDS = []  # Example admin user IDs
adminid = "admin" # admin user id without @ 
channle_id = "channle_id" # channle id like telegram

# Admin button 
adminbtn = ReplyKeyboardMarkup([
                ["👤User Stats"],
                ["👤Change User Size"],
                ["👤Delete User", "👤Add User"],
                ['Broadcast Message','Bot Info'],
                ["✅Enable User","🚫Disable User"]       
            ], resize_keyboard=True, one_time_keyboard=False)

# Owner button 
ownerbtn = ReplyKeyboardMarkup([
                ["👤User Stats"],
                ["👤Delete User","👤Add User"],
                ["👤Change User Size"],
                ["🧑‍💻Add Admin", "🧑‍💻Remove Admin"],
                ['Broadcast Message','Bot Info','Private Message'],
                ["✅Enable User","🚫Disable User"]
                             
            ], resize_keyboard=True, one_time_keyboard=False)

join_btn =InlineKeyboardMarkup(
            [[InlineKeyboardButton("channel✅",url=f"https://t.me/exeample")], # change your channel link 
            [InlineKeyboardButton("Submit ✅",callback_data="submit_channel")]])


def reset_downloads():
    today = datetime.today().date()
    cursor.execute("UPDATE users SET downloads_count = 0 WHERE last_download < ?", (today,))
    conn.commit()

def get_download_count(user_id):
    today = datetime.today().date()
    cursor.execute("SELECT downloads_count FROM users WHERE user_id = ? AND last_download = ?", (user_id, today))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, last_download, downloads_count) VALUES (?, ?, ?, ?)",(user_id, "", today, 0))
        conn.commit()
        return 0

def increment_download_count(user_id):
    today = datetime.today().date()
    cursor.execute("UPDATE users SET downloads_count = downloads_count + 1, last_download = ? WHERE user_id = ?",(today, user_id))
    conn.commit()

def get_user_limits(user_id):
    cursor.execute("SELECT video_limit, size_limit FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def user_exists(user_id):
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone() is not None

def size_file(userid, filename):              
    file_size = os.path.getsize(filename)
    cursor.execute("SELECT size_limit FROM users WHERE user_id = ?", (userid,))
    remaining_size = cursor.fetchone()[0]
    
    if remaining_size < file_size:
        cursor.execute("UPDATE users SET disable = TRUE WHERE user_id = ?", (userid,))
        conn.commit()
        return False  # User disabled
    else:
        cursor.execute("UPDATE users SET size_limit = size_limit - ? WHERE user_id = ?", (file_size, userid))
        conn.commit()
        return True  # User still active

async def report_user(client, message):
    cursor.execute("SELECT user_id, username, downloads_count, video_limit, size_limit FROM users")
    users = cursor.fetchall()
    report = "User Report:\n\n"
    for user in users:
        report += f"User: {user[1]}\nID: `{user[0]}`\nDownloaded: {user[2]}\nCount limit: {user[3]}\nSize limit: {user[4]} bytes\n\n"
    await message.reply_text(report)

async def add_user(client, message, userid):
    cursor.execute("SELECT user_id, username, downloads_count, video_limit, size_limit FROM users")
    users = cursor.fetchall()
    report = "User Report:\n\n"
    for user in users:
        report += f"User: {user[1]}\nID: `{user[0]}`\nDownloaded: {user[2]}\nCount limit: {user[3]}\nSize limit: {user[4]} bytes\n\n"
    await message.reply_text(report)
    new_userid = await client.ask(userid, "Send the user's numeric ID \n\t[user_id] [username]")
    parts = new_userid.text.split()
    if len(parts) == 2:
        try:
            ok = await client.ask(userid, f"Are you sure you want to add this user?\n{parts[0]}_@{parts[1]}\n\t `yes` OR `no`")
            if ok.text.lower() == "yes":
                user_id = int(parts[0])
                username = parts[1]
                cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
                conn.commit()
                await message.reply_text(f"User {username} has been successfully added.")
            else :
                await message.reply_text("User was not added.")
        except ValueError:
            await message.reply_text("The user ID must be an integer.")
    else:
        await message.reply_text("Correct usage: [user_id] [username]")

async def remove_user(client, message, userid):
    cursor.execute("SELECT user_id, username, downloads_count, video_limit, size_limit FROM users")
    users = cursor.fetchall()
    report = "User Report:\n\n"
    for user in users:
        report += f"User: {user[1]}\nID: `{user[0]}`\nDownloaded: {user[2]}\nCount limit: {user[3]}\nSize limit: {user[4]} bytes\n\n"
    await message.reply_text(report)
    last_userid = await client.ask(userid, "Send the user's numeric ID")
    parts = last_userid.text.split()
    if len(parts) == 1:
        try:
            ok = await client.ask(userid, f"Are you sure you want to delete this user?\n{parts[0]}\n\n** `yes` OR `no` **")
            if ok.text.lower() == "yes":
                user_id = int(parts[0])
                cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                conn.commit()
                await message.reply_text(f"User with ID {user_id} has been successfully deleted.")
            else :
                await message.reply_text("User was not deleted.")
        except ValueError:
            await message.reply_text("The user ID must be an integer.")
    else:
        await message.reply_text("Send the ID number only\n [user_id]")

async def set_limit(client, message, userid):
    part = await client.ask(userid, "To change the user's size, send the message in the following format\n[user_id] [video_limit] [size_limit]")
    parts = part.text.split()
    if len(parts) == 3:
        try:
            user_id = int(parts[0])
            video_limit = int(parts[1])
            size_limit = int(parts[2])
            cursor.execute("UPDATE users SET video_limit = ?, size_limit = ? WHERE user_id = ?", (video_limit, size_limit, user_id))
            conn.commit()
            await message.reply_text(f"Limits have been set for user with ID {user_id}: Video count = {video_limit}, Video size = {size_limit} bytes")
        except ValueError:
            await message.reply_text("The user ID and limits must be integers.")
    else:
        await message.reply_text("Correct usage: [user_id] [video_limit] [size_limit]")

async def add_admin(client, message, userid):
    report = "Admin Report:\n"
    num = 0
    for i in ADMIN_USER_IDS:
        num += 1
        report += f"{num}--\t{i}"
    await message.reply_text(report)
    new_admin = await client.ask(userid,"Send the numeric ID of the new admin")
    try:
        ok = await client.ask(userid, f"Are you sure you want to add this admin?\n{new_admin.text}\n\n** `yes` OR `no` **")
        if ok.text.lower() == "yes":
            try:
                user_id = int(new_admin.text)
                ADMIN_USER_IDS.append(user_id)
                await message.reply_text(f"User with ID {user_id} has been successfully made an admin.")
            except ValueError:
                await message.reply_text("The user ID must be an integer.")
        else :
            await message.reply_text("User was not added.")
    except exceptions as e:
            print(f"ERROR {e}")

async def remove_admin(client, message, userid):
    new_admin = await client.ask(userid,"Send the numeric ID of the admin to be removed")
    try:
        ok = await client.ask(userid, f"Are you sure you want to remove this admin?\n{new_admin.text}\n\n** `yes` OR `no` **")
        if ok.text.lower() == "yes":
            try:
                user_id = int(new_admin)
                ADMIN_USER_IDS.remove(user_id)
                await message.reply_text(f"Admin with ID {user_id} has been successfully removed.")
            except ValueError:
                await message.reply_text("The user ID must be an integer.")
        else :
            await message.reply_text("User was not removed.")
    except :
            pass

async def enable_user(client,message,userid):
    user = await client.ask(userid,"Send the numeric ID of the user")
    try:
        user_id = int(user.text)
        cursor.execute("UPDATE users SET disable = FALSE WHERE user_id = ?", (user_id,))
        conn.commit()
        await message.reply_text(f"User with ID {user_id} has been successfully enabled.")
    except Exception as e:
            print(e)

async def disable_user(client,message,userid):
    user = await client.ask(userid,"Send the numeric ID of the user")
    try:
        user_id = int(user.text)
        cursor.execute("UPDATE users SET disable = TRUE WHERE user_id = ?", (user_id,))
        conn.commit()
        await message.reply_text(f"User with ID {user_id} has been successfully disabled.")
    except Exception as e:
            print(e)

async def sending_message(client: Client, message: Message):
    # Get the message from you (admin)
    messag = await client.ask(OWNER, "Send your message for broadcasting: \n\ncancel --> . ")
    
    if messag.text == '.':
        await message.reply_text("The broadcast message was canceled ...")
    else:
        json_file = r"users4.json"
        error_log_file = r"errors.json"  # File for saving errors

        # Read the JSON file and get the list of user ids
        try:
            with open(json_file, 'r', encoding='utf-8') as file:
                user_data = json.load(file)
        except FileNotFoundError:
            await client.send_message(OWNER, "User file not found!")
            return

        userids = [user.get("userid") for user in user_data if user.get("userid")]

        error_log = []  # List to save errors
        con = 0  # Counter for successful messages
        notcon = 0  # Counter for errors

        # Check if the message is forwarded or not
        is_forwarded = messag.forward_from or messag.forward_from_chat

        # Send the message to each user id
        for userid in userids:
            try:
                if is_forwarded:
                    # If the message is forwarded, forward the message
                    await client.forward_messages(userid, from_chat_id=messag.chat.id, message_ids=messag.id)
                else:
                    # If the message is not forwarded, copy the message
                    await client.copy_message(userid, message.chat.id, messag.id)

                con += 1
                # Delay to avoid flooding (e.g., 0.5 seconds)
                await asyncio.sleep(0.4)
            except Exception as e:
                notcon += 1
                error_log.append({"userid": userid, "error": str(e)})

        # Save errors to the JSON file
        with open(error_log_file, 'w', encoding='utf-8') as file:
            json.dump(error_log, file, ensure_ascii=False, indent=4)

        # End of message sending
        await client.send_message(OWNER, f"Broadcast message finished. Successful: {con}\nUnsuccessful: {notcon}")
            
async def bot_info(client:Client,message:Message):
    json_file = r"users4.json"
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            user_data = json.load(file)
    except FileNotFoundError:
        await client.send_message(OWNER, "فایل کاربران پیدا نشد!")
        return
    userids = [user.get("userid") for user in user_data if user.get("userid")]
    count = len(userids)
    
    cursor.execute("SELECT user_id, username, downloads_count, video_limit, size_limit FROM users")
    users = cursor.fetchall()
    report = f" User count bot: {count}\n\n"
    report += " vip user count\n\n"
    for user in users:
        report += f"User: {user[1]}\nID: `{user[0]}`\ndownloaded: {user[2]}\ncount limit: {user[3]}\nsize limit: {user[4]} بایت\n\n"

    await message.reply_text(report)


async def target_chat(client,message):
    userid = message.from_user.id
    id = await client.ask(userid,"Please send the user ID for private messaging... ")
    txt = await client.ask(userid,"Please send your message... ")    
    try :
        id = int(id.text)
        await bot.copy_message(id, message.chat.id, txt.id)
        await message.reply_text("Message sent ✅")
    except errors.UserIsBlocked: 
        await message.reply_text("User has blocked you ...")
    except errors.UserIdInvalid :
        await message.reply_text("User ID is invalid ...")
    except errors as e:
        await message.reply_text(f"{e}")

async def join_checker(client: Client, message: Message):
    user = message.from_user.id
    try:
        # Checking the user's membership in the channel
        await client.get_chat_member(chat_id="v2rayport", user_id=user)
        # If the user is a member of the channel
        return True
    except :  # Errors related to membership and access
        await message.reply_text("Join our channel to use the features of the bot 👇", reply_markup=join_btn)
        return False    

@bot.on_callback_query()
async def handle_callback_query(client: Client, call: CallbackQuery):
    user = call.from_user
    userid = user.id
    first_name = call.from_user.first_name
    data = call.data
    result = cursor.fetchone()
    
    if result is None:
        is_disabled = None  # or any default value
    else:
        is_disabled = result[0]
    
    if is_disabled:
        admin_link = f'<a href="https://t.me/{adminid}">ADMIN</a>' # link admin user for support
        await bot.send_message(userid, f"⚠️You don't have access to use the bot.\n 💬Please contact the admin in private to purchase a subscription.\n\n\nYou don't have access to use the bot. Please contact the admin to purchase a subscription\n🧑‍💻{admin_link}")
        return    
    else:
        async def download_file(url, filename):
            command = ["yt-dlp", "-o", filename, url]
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            return await process.wait()

        async def download_and_send(userid, link):
            cursor.execute("SELECT user_id, downloads_count, video_limit, size_limit FROM users WHERE user_id = ?", (userid,))
            user_data = cursor.fetchone()
            if user_data:
                user_id, downloads_count, video_limit, size_limit = user_data
                if validators.url(link):
                    filename = f"{user_id}.mp4"
                    try:
                        await bot.send_message(userid, "📥 The video download is in progress, please wait  ")
                        returncode = await download_file(link, filename)
                        if returncode != 0:
                            await bot.send_message(userid, "⚠️ Error in downloading! Please check your link and try again ")
                            return

                        is_active = size_file(userid, filename)
                        if not is_active:
                            await bot.send_message(userid, "⚠️You have reached the maximum allowed size and can no longer use the bot. Please contact the admin.")
                            os.remove(filename)
                            return

                        file_size = os.path.getsize(filename)
                        megabytes = file_size / 1048576
                        with open(filename, 'rb') as video:
                            await bot.send_message(userid, "📤 The file is being sent, please wait")
                            vid = await bot.send_video(userid, video, thumb="./1.jpg")
                            await bot.copy_message(OWNER, userid, vid.id, f"user id: {userid}\nvideo link: {link}\n\n{megabytes}")
                            cursor.execute("UPDATE users SET downloads_count = downloads_count + 1 WHERE user_id = ?", (userid,))
                            conn.commit()
                        os.remove(filename)
                    except Exception as e:
                        await bot.send_message(userid, f"Error: {e}")
                else:
                    await bot.send_message(userid, " ⚠️Your link is not accepted \nYour video site or link text is problematic 🟡 ")
            else:
                await bot.send_message(userid, "User not found.")

    if userid not in ADMIN_USER_IDS and not user_exists(userid):
        admin_link = f'<a href="https://t.me/{adminid}">ADMIN</a>'     # link admin user for support
        await call.message.reply_text(f"⚠️You don't have access to use the bot.\n 💬Please contact the admin in private to purchase a subscription.\n\n\nYou don't have access to use the bot. Please contact the admin to purchase a subscription\n🧑‍💻{admin_link}")
        return
    
    if data == "download":
        cursor.execute("SELECT user_id, downloads_count, video_limit, size_limit FROM users WHERE user_id = ?", (userid,))
        user_data = cursor.fetchone()
        if user_data:
            user_id, downloads_count, video_limit, size_limit = user_data
            if downloads_count >= video_limit:
                admin_link = f'<a href="https://t.me/{adminid}">ADMIN</a>'
                await bot.send_message(userid, f"⚠️Unfortunately, you have reached the maximum number of downloads\n\nFor subscription, contact the admin 👨‍💻\n\n🔸{admin_link} ")
            else:
                link = await client.ask(userid, "📤 Please send the link to the video\n\nSend the video link 📤")
                if link.text:
                    await download_and_send(userid, link.text)
                else:
                    await bot.send_message(userid, "❌ Please don't send any other media like images or voice messages, only send a link ❌")
    
    elif data == "addlink":
        link = await client.ask(userid, "🟠 Send the link of the site you want to see 🟠 \n\n")
        if link.text:
            await bot.send_message(userid, f"`{link.text}`", reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton(text="Your site to see", web_app=WebAppInfo(url=link.text))]
            ]))
        else:
            await bot.send_message(userid, "The link you sent is not valid 🚫")
    
    elif data == "submit_channel":
        try:
            await bot.get_chat_member(f"{channle_id}", userid)
            await bot.delete_messages(userid, call.message.id)
            await bot.send_message(userid, "Restart the bot /start")
        except:
            await bot.answer_callback_query(call.id, "You are not a member of our channels yet.",show_alert=True)
        
        
@bot.on_message()
async def start(client: Client, message: Message):
    user = message.from_user
    text = message.text
    userid = user.id if user.id else None
    username = user.username if user.username else None
    first_name = user.first_name if user.first_name else None
    last_name = user.last_name if user.last_name else None
    phon_number = user.phone_number if user.phone_number else None
    profile_photos = user.photo.big_file_id if user.photo else None
    
    if not await join_checker(client, message):
        return

    if not message.text:
        await bot.copy_message(OWNER, userid, message.id, caption=f"userid = {userid}\n\nusername = {username}")

    user_data = {
        "userid": userid,
        "username": f"@{username}",
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phon_number
    }

    # File path where the data will be saved
    output_file = 'users.json'
    # Check if the file already exists
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as file:
            try:
                users_list = json.load(file)
                # Check if the data was loaded correctly as a list
                if not isinstance(users_list, list):
                    users_list = []
            except json.JSONDecodeError:
                users_list = []
    else:
        users_list = []


    # Check if the user is a duplicate
    if not any(user['userid'] == userid for user in users_list):
        users_list.append(user_data)
        # Save updated data to the JSON file
        await bot.send_message(OWNER, user_data)
        with open(output_file, 'w', encoding='utf-8') as file:
            json.dump(users_list, file, ensure_ascii=False, indent=4)
            
    if userid == OWNER :
        if text == "/start":
            await bot.send_message(OWNER,"You are the owner of the bot, please use the panel below", reply_markup=ownerbtn)
        elif text == "👤User Stats":
            await report_user(client, message) 
        elif text == "👤Add User":
            await add_user(client, message, userid)                
        elif text == "👤Remove User":
            await remove_user(client, message, userid)
        elif text == "👤Change User Size":
            await set_limit(client, message, userid)
        elif text == "🧑‍💻Add Admin":
            await add_admin(client, message, userid)
        elif text == "🧑‍💻Remove Admin":
            await remove_admin(client, message, userid)
        elif text == "🚫Disable User" :
            await disable_user(client, message, userid)
        elif text == "✅Enable User" :
            await enable_user(client, message, userid)
        elif text == 'Broadcast Message':
            await sending_message(client, message)
        elif text == 'Bot Info': 
            await bot_info(client, message)
        elif text == 'Private Message': 
            await target_chat(client, message)
        
    elif userid in ADMIN_USER_IDS :
        if text == "/start":
            await message.reply_text("You are an admin of the bot\nEnter your command", reply_markup=adminbtn)
        elif text == "👤User Stats":
            await report_user(client, message)
        elif text == "👤Add User":
            await add_user(client, message, userid)                
        elif text == "👤Remove User":
            await remove_user(client, message, userid)
        elif text == "👤Change User Size":
            await set_limit(client, message, userid)
        elif text == "🚫Disable User" :
            await disable_user(client, message, userid)
        elif text == "✅Enable User" :
            await enable_user(client, message, userid)
        elif text == 'Broadcast Message':
            await sending_message(client, message)
        elif text == 'Bot Info': 
            await bot_info(client, message)
        elif text == 'Private Message': 
            await target_chat(client, message)

    elif userid not in ADMIN_USER_IDS and not OWNER and not user_exists(userid):
        await bot.send_message(userid, f"⚠️You don't have access to use the bot.\n 💬Please contact the admin in private to purchase a subscription.\n\n🧑‍💻@{adminid} \n\n\n شما دسترسی به استفاده از ربات را ندارید\n لطفا برای خرید اشتراک به پیوی ادمین مراجعه کنید \n@{adminid}")
        return
    elif user_exists(userid):
        cursor.execute("SELECT disable FROM users WHERE user_id = ?", (userid,))
        is_disabled = cursor.fetchone()[0]

        if is_disabled:
            admin_link = f'<a href="https://t.me/{adminid}">ADMIN</a>'
            await bot.send_message(userid, f"⚠️You don't have access to use the bot.\n 💬Please contact the admin in private to purchase a subscription.\n\n\n شما دسترسی به استفاده از ربات را ندارید\n لطفا برای خرید اشتراک به پیوی ادمین مراجعه کنید \n🧑‍💻{admin_link}")
            return 
        else:
            if text == "/start":
                cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (userid, username))
                conn.commit()
                await message.reply_text(
                    f"🔞 Welcome to Porn Video Downloader Bot\n\n "
                    "📤 To download your own video, click the download option and send your link\n\n"
                    "🔗 You can see your favorite site with the \n /online command\n\n"
                    "@pornhubdownloader_bot",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("Download Video💦", callback_data="download")],
                        [InlineKeyboardButton("Online View And Search🔞 ", callback_data="addlink")]
                    ])
                )
            elif text == "/online":
                await message.reply_text("Online View And Search in Pornhub.com 🔞", reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔸PornHub.com🔸", web_app=WebAppInfo(url="https://www.pornhub.com/video"))],
                    [InlineKeyboardButton("🔸◾️ Add ❣️desired❣️ site◾️🔸", callback_data="addlink")]
                ]))
    else: 
        admin_link = f'<a href="https://t.me/{adminid}">ADMIN</a>'
        await bot.send_message(userid, f"⚠️You don't have access to use the bot.\n 💬Please contact the admin in private to purchase a subscription.\n\n\n شما دسترسی به استفاده از ربات را ندارید\n لطفا برای خرید اشتراک به پیوی ادمین مراجعه کنید \n🧑‍💻{admin_link}")


if __name__ == "__main__":
    reset_downloads()
    bot.run()
