from src.pybaileys.client import BaileysClient
import time
import base64

client = BaileysClient()
client.start()

# 1. Handle New Messages (messages.upsert)
@client.on('messages.upsert')
def on_new_message(data):
    print("\n--- NEW MESSAGE ---")
    for msg in data.get('messages', []):
        remote_jid = msg.get('key', {}).get('remoteJid')
        push_name = msg.get('pushName', 'Unknown')
        
        # Check for text message
        text = msg.get('message', {}).get('conversation')
        if not text:
            text = msg.get('message', {}).get('extendedTextMessage', {}).get('text')
            
        print(f"From: {push_name} ({remote_jid})")
        print(f"Content: {text}")

        if text == '.ping':
            client.sendMessage(remote_jid, {'text': 'Pong!'})

# 2. Handle Contact Updates (contacts.upsert)
@client.on('contacts.upsert')
def on_contacts(data):
    print(f"\n[Contacts] Syncing {len(data)} contacts...")
    # data is a list of contacts
    for contact in data:
        print(f"- {contact.get('id')}: {contact.get('name')}")

# 3. Handle Credentials Update (creds.update)
@client.on('creds.update')
def on_creds(data):
    print("\n[System] Auth credentials updated")

# 4. Handle Connection Updates (connection.update)
@client.on('connection.update')
def on_connection(data):
    status = data.get('connection')
    qr = data.get('qr')
    
    if status == 'open':
        print("\n[Connection] ✅ Connected successfully!")
    elif status == 'close':
        print("\n[Connection] ❌ Connection closed")
    elif qr:
        print("\n[Connection] 📷 QR Code received (Scan it in terminal)")

# Keep the script running
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    client.stop()