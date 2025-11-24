from src.pybaileys.client import BaileysClient
import time
import sys
import qrcode
import json
import os

# Force output
sys.stdout.reconfigure(line_buffering=True)

client = BaileysClient()

print("--- WHATSAPP ALL-TYPES TESTER ---")
print("Send '.test all' to your bot to run the sequence.")

# Valid Raw Image URL
TEST_IMAGE_URL = "https://raw.githubusercontent.com/AlexaInc/alexa-v3/main/res/img/alexa.png"

try:
    client.start(
        auth_path="my_session_folder",
        log_level='error',
        browser=['Alexa Bot', 'Chrome', '1.0.0'],
        connectTimeoutMs=60000
    )

    @client.on('messages.upsert')
    def on_new_message(data):
        messages = data.get('messages', [])
        for msg in messages:
            if msg.get('key', {}).get('fromMe'): continue

            remote_jid = msg.get('key', {}).get('remoteJid')
            msg_content = msg.get('message', {})
            text = (msg_content.get('conversation') or msg_content.get('extendedTextMessage', {}).get('text'))

            if not text: continue
            
            if text.lower().strip() == '.test all':
                print(f"\n[START] Sending all message types to {remote_jid}...")

                # 1. TEXT MESSAGE
                print("[1/10] Sending Text...")
                client.sendMessage(remote_jid, {'text': '1. Simple Text Message'})
                time.sleep(2)

                # 2. LOCATION
                print("[2/10] Sending Location...")
                client.sendMessage(remote_jid, {
                    'location': {
                        'degreesLatitude': 24.121231,
                        'degreesLongitude': 55.1121221
                    }
                })
                time.sleep(2)

                # 3. CONTACT
                print("[3/10] Sending Contact...")
                vcard = "BEGIN:VCARD\nVERSION:3.0\nFN:Hansaka\nTEL;type=CELL;waid=94740970377:+94 74 097 0377\nEND:VCARD"
                client.sendMessage(remote_jid, {
                    'contacts': {
                        'displayName': 'Hansaka',
                        'contacts': [{'vcard': vcard}]
                    }
                })
                time.sleep(2)

                # 4. POLL
                print("[4/10] Sending Poll...")
                client.sendMessage(remote_jid, {
                    'poll': {
                        'name': 'Is Baileys Python working?',
                        'values': ['Yes', 'No'],
                        'selectableCount': 1
                    }
                })
                time.sleep(2)

                # 5. IMAGE (Media)
                print("[5/10] Sending Image...")
                client.sendMessage(remote_jid, {
                    'image': {'url': TEST_IMAGE_URL},
                    'caption': '5. Image from URL'
                })
                time.sleep(2)

                # 6. VIDEO (Media)
                print("[6/10] Sending Video...")
                client.sendMessage(remote_jid, {
                    'video': {'url': 'https://www.w3schools.com/html/mov_bbb.mp4'},
                    'caption': '6. Video Test',
                    'gifPlayback': False
                })
                time.sleep(2)

                # 7. AUDIO (Media)
                print("[7/10] Sending Audio...")
                client.sendMessage(remote_jid, {
                    'audio': {'url': 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3'},
                    'mimetype': 'audio/mp4',
                    'ptt': True
                })
                time.sleep(2)

                # 8. INTERACTIVE MENU (Your Custom Structure)
                print("[8/10] Sending Interactive Menu...")
                
                # Define the buttons exactly as requested
                buttons = [
                    {
                        "name": "single_select",
                        "buttonParamsJson": json.dumps({
                            "title": "Select a menu to open",
                            "sections": [{
                                "title": "select a Menu",
                                "rows": [
                                    {"header": " ", "title": "Main", "id": ".menu_util"},
                                    {"header": " ", "title": "Stickers", "id": ".menu_sticker"},
                                    {"header": " ", "title": "Websearch", "id": ".menu_web"},
                                    {"header": " ", "title": "Youtube", "id": ".menu_svm"},
                                    {"header": " ", "title": "Groups manage", "id": ".menu_groups"},
                                    {"header": " ", "title": "NSFW", "id": ".menu_nsfw"},
                                    {"header": " ", "title": "SFW", "id": ".menu_sfw"},
                                    {"header": " ", "title": "Fun features", "id": ".menu_games"}
                                ]
                            }]
                        })
                    },
                    {
                        "name": "cta_url",
                        "buttonParamsJson": json.dumps({
                            "display_text": "Contact Owner",
                            "url": "https://wa.me/94740970377?text=hello"
                        })
                    }
                ]

                # Use the flat structure supported by the library (no viewOnceMessage wrapper)
                interactive_message = {
                    "image": {"url": TEST_IMAGE_URL},
                    "caption": "👋 *Hello! Welcome to Alexa Bot*",
                    "footer": "Powered by HANSAKA",
                    "interactiveButtons": buttons,
                    # The library might require this for image buttons
                    "hasMediaAttachment": True 
                }

                try:
                    # Pass the interactive_message directly as content
                    client.sendMessage(remote_jid, interactive_message)
                    print("   [SUCCESS] Interactive Menu Sent!")
                except Exception as e:
                    print(f"   [FAIL] Interactive Menu Error: {e}")
                time.sleep(2)

                # 9. SIMPLE BUTTONS (Legacy)
                print("[9/10] Sending Simple Buttons...")
                client.sendMessage(remote_jid, {
                    "text": "Simple Buttons Test",
                    "footer": "Footer",
                    "buttons": [
                        {"buttonId": "id1", "buttonText": {"displayText": "Button 1"}},
                        {"buttonId": "id2", "buttonText": {"displayText": "Button 2"}}
                    ]
                })
                time.sleep(2)

                print("\n[DONE] All tests finished.")

    @client.on('connection.update')
    def on_conn(data):
        if data.get('qr'): 
            print("\n[QR CODE RECEIVED]")
            qr = qrcode.QRCode()
            qr.add_data(data['qr'])
            qr.print_ascii(invert=True)
        if data.get('connection') == 'open': 
            print("\n[SUCCESS] Connected!")

    print("Client running... Send '.test all' to your bot.")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    client.stop()