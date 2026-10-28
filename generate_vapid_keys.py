"""
Creates the keys that let your server send "Mr. Sensei replied" push notifications.

    pip install pywebpush
    python generate_vapid_keys.py

It writes vapid_private.pem next to this file and prints two lines to paste into your .env.
Keep vapid_private.pem secret (never share it or commit it). Create the keys ONCE: if you
make new ones later, every phone has to turn notifications on again.
"""
import base64
from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization

v = Vapid()
v.generate_keys()
v.save_key("vapid_private.pem")

public_bytes = v.public_key.public_bytes(
    serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
)
public_b64 = base64.urlsafe_b64encode(public_bytes).decode().rstrip("=")

print("\nAdd these lines to your .env file, then restart the server:\n")
print(f"VAPID_PUBLIC_KEY={public_b64}")
print("VAPID_PRIVATE_KEY_FILE=vapid_private.pem")
print("VAPID_SUBJECT=mailto:you@example.com   # use your real email address\n")