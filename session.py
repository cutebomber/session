"""
Session Creator
---------------
Run this on your LOCAL PC to log into Telegram accounts
and save session strings directly into the bot's database.

Usage:
    pip install telethon
    python session_creator.py

It will ask for phone number, OTP, and optional 2FA password.
Then saves the session to bot_data.db automatically.

Copy bot_data.db to your VPS after adding all accounts,
OR just note down the session strings and add them manually.
"""

import asyncio
import sqlite3
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    FloodWaitError,
)

# ── Paste your API_ID and API_HASH from my.telegram.org ──
API_ID   = 21752358
API_HASH = "fb46a136fed4a4de27ab057c7027fec3"
DB_PATH  = "bot_data.db"   # will be created here if not exists


# ── DB helpers ────────────────────────────────────────

def init_db():
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone TEXT UNIQUE,
            password_2fa TEXT,
            session_string TEXT,
            status TEXT DEFAULT 'available',
            added_at TEXT,
            sold_at TEXT,
            buyer_id INTEGER
        )
    """)
    con.commit()
    con.close()


def save_session(phone: str, password_2fa: str, session_string: str):
    con = sqlite3.connect(DB_PATH)
    con.execute("""
        INSERT INTO accounts (phone, password_2fa, session_string, status, added_at)
        VALUES (?, ?, ?, 'available', ?)
        ON CONFLICT(phone) DO UPDATE SET
            password_2fa   = excluded.password_2fa,
            session_string = excluded.session_string,
            status         = 'available',
            added_at       = excluded.added_at
    """, (phone, password_2fa, session_string, datetime.now().strftime("%Y-%m-%d %H:%M")))
    con.commit()
    con.close()


def list_accounts():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    rows = con.execute("SELECT phone, status, added_at FROM accounts ORDER BY added_at DESC").fetchall()
    con.close()
    return [dict(r) for r in rows]


# ── Main login flow ───────────────────────────────────

async def add_account():
    print("\n" + "="*50)
    phone = input("📱 Enter phone number (with country code, e.g. +14155552671): ").strip()

    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.connect()

    try:
        result = await client.send_code_request(phone)
        print(f"\n✅ OTP sent to {phone}")
        print("👉 Check Telegram app on that phone for a message from 'Telegram'")
    except FloodWaitError as e:
        print(f"\n❌ Flood wait — try again in {e.seconds} seconds.")
        await client.disconnect()
        return
    except Exception as e:
        print(f"\n❌ Error sending OTP: {e}")
        await client.disconnect()
        return

    code = input("\n🔑 Enter the OTP code: ").strip().replace(" ", "")

    password_2fa = ""
    try:
        await client.sign_in(phone, code, phone_code_hash=result.phone_code_hash)

    except SessionPasswordNeededError:
        print("\n🔒 2FA is enabled on this account.")
        password_2fa = input("🔑 Enter 2FA password: ").strip()
        try:
            await client.sign_in(password=password_2fa)
        except Exception as e:
            print(f"\n❌ Wrong 2FA password: {e}")
            await client.disconnect()
            return

    except PhoneCodeInvalidError:
        print("\n❌ Invalid OTP code. Try again.")
        await client.disconnect()
        return

    except Exception as e:
        print(f"\n❌ Login error: {e}")
        await client.disconnect()
        return

    # Save session
    session_string = client.session.save()
    await client.disconnect()

    save_session(phone, password_2fa, session_string)

    print(f"\n✅ Account {phone} saved successfully!")
    print(f"📋 Session string (first 40 chars): {session_string[:40]}...")


async def main():
    init_db()
    print("\n╔══════════════════════════════════════╗")
    print("║      Fragment Bot — Session Creator  ║")
    print("╚══════════════════════════════════════╝")

    while True:
        print("\nOptions:")
        print("  1. Add account")
        print("  2. List saved accounts")
        print("  3. Exit")

        choice = input("\nChoice: ").strip()

        if choice == "1":
            await add_account()

        elif choice == "2":
            accounts = list_accounts()
            if not accounts:
                print("\n⚠️  No accounts saved yet.")
            else:
                print(f"\n📦 {len(accounts)} account(s) in database:\n")
                for a in accounts:
                    print(f"  ✅ {a['phone']}  |  {a['status']}  |  {a['added_at']}")

        elif choice == "3":
            print("\n👋 Done! Copy bot_data.db to your VPS.")
            print("   Or run: scp bot_data.db root@YOUR_VPS_IP:~/i/bot_data.db")
            break

        else:
            print("Invalid choice.")


if __name__ == "__main__":
    asyncio.run(main())
