from pybaileys import BaileysClient
import time
import sys
import qrcode

# Force output to appear immediately
sys.stdout.reconfigure(line_buffering=True)

print("--- TESTING INSTALLED PACKAGE: pybaileys ---")

client = BaileysClient()

try:
    # We use a new session folder for this test
    print("1. Initializing Client...")
    client.start(auth_path="installed_package_session")

    @client.on('connection.update')
    def on_conn(data):
        if data.get('qr'):
            print("\n[SUCCESS] QR Code received from installed package!")
            qr = qrcode.QRCode()
            qr.add_data(data['qr'])
            qr.print_ascii(invert=True)
            # print("The package is working correctly.")
            
        if data.get('connection') == 'open':
            print("\n[SUCCESS] Connected to WhatsApp!")

    print("Waiting for engine to start...")
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("Stopping...")
    client.stop()
except Exception as e:
    print(f"Error: {e}")