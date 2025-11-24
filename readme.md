

# 🎉 **PyBaileys – WhatsApp Web API for Python**

<div align="center">
  <img src="https://github.com/Fluid-Studio/Fluid-Studio/raw/main/assets/logo.png" width="150" />
  <h3>A powerful Python wrapper around the Baileys WhatsApp Web API</h3>
  <strong>Write WhatsApp bots fully in Python while a Node.js engine runs silently in the background.</strong>
</div>



## ✨ Features

* 🐍 **Pure Python API** — Create bots without touching Node.js code
* ⚡ **Auto Setup** — Auto-downloads & configures Node.js on first run
* 🔐 **Multi-Device Support**
* 🖼️ **Send All Message Types** (text, images, videos, audio, location, polls)
* 🧩 **Interactive Native Flow Buttons / Lists**
* 🔄 **Event-based architecture**

---

## 📦 Installation

```bash
pip install pybaileys
```

> ⏳ *On first run, PyBaileys installs a Node.js runtime automatically. This may take a minute.*

---

## 🚀 Quick Start

```python
from pybaileys import BaileysClient
import time
import qrcode

Alexainc = BaileysClient()

# 1. Connection + QR
@Alexainc.on('connection.update')
def on_connection(data):
    if data.get('qr'):
        qr = qrcode.QRCode()
        qr.add_data(data['qr'])
        qr.print_ascii(invert=True)
        print("Scan the QR Code above!")

    if data.get('connection') == 'open':
        print("✅ Connected successfully!")

# 2. Incoming Messages
@Alexainc.on('messages.upsert')
def on_message(data):
    for msg in data.get('messages', []):
        if msg.get('key', {}).get('fromMe'):
            continue

        remote_jid = msg['key']['remoteJid']
        print(f"New message from {remote_jid}")

# 3. Start
try:
    Alexainc.start(auth_path="session_folder")
    print("Alexainc started. Waiting for events...")
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    Alexainc.stop()
```

---

## ⚙️ Configuration

```python
Alexainc.start(
    auth_path="my_session",
    log_level="error",
    browser=["My Python Bot", "Chrome", "1.0.0"],
    connectTimeoutMs=60000,
    defaultQueryTimeoutMs=60000,
    syncFullHistory=False
)
```

---

# 💬 Sending Messages

### **Text Message**

```python
Alexainc.sendMessage(remote_jid, {"text": "Hello World!"})
```

---

### **Image / Video / Audio**

```python
# Image
Alexainc.sendMessage(remote_jid, {
    "image": {"url": "https://example.com/image.png"},
    "caption": "Check this out!"
})

# Video
Alexainc.sendMessage(remote_jid, {
    "video": {"url": "https://example.com/video.mp4"},
    "caption": "My Video",
    "gifPlayback": False
})

# Voice Note (PTT)
Alexainc.sendMessage(remote_jid, {
    "audio": {"url": "https://example.com/audio.mp3"},
    "mimetype": "audio/mp4",
    "ptt": True
})
```

---

### **Location**

```python
Alexainc.sendMessage(remote_jid, {
    "location": {
        "degreesLatitude": 6.9271,
        "degreesLongitude": 79.8612
    }
})
```

---

### **Poll**

```python
Alexainc.sendMessage(remote_jid, {
    "poll": {
        "name": "Do you like Python?",
        "values": ["Yes", "No"],
        "selectableCount": 1
    }
})
```

---

## 🧩 Interactive Native Flow Buttons (Latest WhatsApp UI)

```python
import json
import uuid

buttons = [
    {
        "name": "single_select",
        "buttonParamsJson": json.dumps({
            "title": "Click to open menu",
            "sections": [{
                "title": "Main Menu",
                "rows": [
                    {"title": "Option 1", "id": "opt_1"},
                    {"title": "Option 2", "id": "opt_2"}
                ]
            }]
        })
    },
    {
        "name": "cta_url",
        "buttonParamsJson": json.dumps({
            "display_text": "Visit Website",
            "url": "https://google.com",
            "merchant_url": "https://google.com"
        })
    }
]

payload = {
    "message": {
        "messageContextInfo": {
            "deviceListMetadata": {},
            "deviceListMetadataVersion": 2
        },
        "interactiveMessage": {
            "body": {"text": "👋 *Interactive Menu*"},
            "footer": {"text": "Powered by PyBaileys"},
            "header": {
                "title": "MENU",
                "subtitle": "Select an option",
                "hasMediaAttachment": False
            },
            "nativeFlowMessage": {"buttons": buttons}
        }
    }
}

msg_id = "WA" + uuid.uuid4().hex[:12].upper()
Alexainc.relayMessage(remote_jid, payload, {
    "messageId": msg_id,
    "participant": {"jid": remote_jid}
})
```

---

# 🔔 Events

| Event               | Description                  |
| ------------------- | ---------------------------- |
| `connection.update` | QR code / connection updates |
| `creds.update`      | Session credentials updated  |
| `messages.upsert`   | New messages                 |
| `contacts.upsert`   | Contacts updated             |
| `groups.update`     | Group metadata updated       |

---

# 🧠 Advanced Utilities

```python
# Random Message ID
msg_id = Alexainc.utils.generateMessageID()

# Disconnect reason
reason = Alexainc.utils.DisconnectReason.loggedOut
```

---

# 🛠 Troubleshooting

### ❌ *"Node.js not found"*

→ Install Node.js 18+ or let PyBaileys auto-install it.

### ❌ *401 Unauthorized*

→ Delete your session folder and scan QR again.

### ❌ *Slow first startup*

→ Node.js environment is being installed and compiled.

---

# ❤️ Credits

PyBaileys is a wrapper around the amazing
👉 [https://github.com/WhiskeySockets/Baileys](https://github.com/WhiskeySockets/Baileys)

---

If you want, I can also:

✅ Export this README as **PDF / DOCX / MD file**
✅ Add badges (version, status, Python version, downloads)
✅ Add logo, colors, and styled headings for your brand **HANSAKA GFX**

Just tell me!
