import requests
import json
import time

# Configuration
API_URL = "https://your-backend-url.vercel.app/whatsapp/webhook" # Update this after deploy
# For local testing: 
# API_URL = "http://127.0.0.1:8000/whatsapp/webhook"

def send_mock_message(phone, message):
    payload = {
        "object": "simulator", # This triggers the simulator logic in your whatsapp.py
        "sender": phone,
        "message": message,
        "id": f"sim_{int(time.time())}"
    }
    
    print(f"[*] Sending: '{message}' from {phone}...")
    try:
        response = requests.post(API_URL, json=payload)
        if response.status_code == 200:
            print("[+] Success! Check your Dashboard.")
            print(f"Server Response: {response.json()}")
        else:
            print(f"[-] Failed (Status {response.status_code}): {response.text}")
    except Exception as e:
        print(f"[-] Error connecting to backend: {e}")

if __name__ == "__main__":
    print("--- OmniFetch WhatsApp Simulator ---")
    print("Use this to simulate customer messages during your demo.")
    
    while True:
        phone = input("\nCustomer Phone (e.g. +50688888888): ")
        if not phone: phone = "+50688888888"
        
        msg = input("Message Content: ")
        if not msg: continue
        
        send_mock_message(phone, msg)
