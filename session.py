"""
Session String Generator
-------------------------
Run on your PC. Logs into a Telegram account and prints the session string.
Copy that string and paste it into the bot's "Add Account" flow.

Install: pip install telethon
Run:     python gen_session.py
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError

API_ID   = 21752358
API_HASH = "fb46a136fed4a4de27ab057c7027fec3"


async def main():
    phone = input("📱 Phone number (with country code): ").strip()

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    try:
        result = await client.send_code_request(phone)
        print("✅ OTP sent — check Telegram app on that phone")
    except FloodWaitError as e:
        print(f"❌ Flood wait, try again in {e.seconds}s")
        return
    except Exception as e:
        print(f"❌ Error: {e}")
        return

    code = input("🔑 Enter OTP: ").strip().replace(" ", "")

    try:
        await client.sign_in(phone, code, phone_code_hash=result.phone_code_hash)

    except SessionPasswordNeededError:
        pw = input("🔒 2FA password: ").strip()
        try:
            await client.sign_in(password=pw)
        except Exception as e:
            print(f"❌ Wrong 2FA: {e}")
            return

    except PhoneCodeInvalidError:
        print("❌ Invalid OTP")
        return

    except Exception as e:
        print(f"❌ {e}")
        return

    session_string = client.session.save()
    await client.disconnect()

    print("\n" + "="*60)
    print("✅ SUCCESS — Copy the line below and paste it into the bot:")
    print("="*60)
    print(f"{phone}|{session_string}")
    print("="*60)
    print("\nIn the bot: Admin Panel → Add Account → Paste Session String")
    print("Then paste the whole line above (phone|session format).")


asyncio.run(main())
