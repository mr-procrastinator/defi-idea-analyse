import os
from dotenv import load_dotenv
import requests
import time

load_dotenv()
# Telegram configuration
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

def get_all_users():
    """Get all unique users who have interacted with the bot"""
    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    users = set()
    
    try:
        response = requests.get(telegram_url)
        if response.ok:
            print("✅ Updates retrieved successfully!")
            updates = response.json()['result']
            
            # Extract user IDs from updates
            for update in updates:
                if 'message' in update:
                    user_id = update['message']['from']['id']
                    first_name = update['message']['from'].get('first_name', 'Unknown')
                    username = update['message']['from'].get('username', 'Unknown')
                    users.add((user_id, first_name, username))
            
            return users
        else:
            print("❌ Failed to get updates")
            print(f"Error: {response.text}")
            return set()
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return set()

def broadcast_message(users, message):
    """
    Send message to all users
    
    Args:
        users (set): Set of tuples containing (user_id, first_name, username)
        message (str): Message to broadcast to all users
    """

    telegram_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    print(f"\nBroadcasting message to {len(users)} users:")
    for user_id, first_name, username in users:
        try:
            payload = {
                "chat_id": user_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            print(f"\nSending to {first_name} (@{username})...")
            response = requests.post(telegram_url, json=payload)
            
            if response.ok:
                print(f"✅ Message sent successfully!")
            else:
                print(f"❌ Failed to send message")
                print(f"Error: {response.text}")
            
            # Sleep briefly to avoid hitting rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Error sending to user {user_id}: {str(e)}")

if __name__ == "__main__":
    print("Step 1: Getting all users who have interacted with the bot...")
    users = get_all_users()
    
    if users:
        print(f"\nFound {len(users)} users:")
        for user_id, first_name, username in users:
            print(f"- {first_name} (@{username})")
        
        # Example message
        test_message = "🔔 Custom Broadcast Message!\n\n" \
                      "ID: TEST456\n" \
                      "Message: This is a custom broadcast test\n" \
                      "Time: " + time.strftime("%Y-%m-%d %H:%M:%S")
        
        print("\nStep 2: Broadcasting custom message...")
        broadcast_message(users, test_message)
    else:
        print("\n❌ No users found. Make sure some users have interacted with the bot first.")