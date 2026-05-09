# Enterprise AI CRM: Deployment & Demo Guide

This guide ensures your $0 infrastructure is solid for the pilot.

## 1. Environment Setup (Local Machine)
1.  **Groq:** Open `server/.env` and paste your `gsk_...` key.
2.  **Ngrok:** Ensure you are logged into Ngrok (`ngrok config add-authtoken ...`).

## 2. Launching the Demo
1.  **Backend:** Right-click `start_demo.ps1` and select "Run with PowerShell".
2.  **Tunnel:** In a new terminal, run: `ngrok http 8000`.
3.  **Frontend:** 
    *   Go to `client/`
    *   Run `npm install` (first time only)
    *   Run `npm run dev`

## 3. Connecting to Supabase ($0 Database)
If you move away from the local `sql_app.db`:
1.  Create a project on [Supabase](https://supabase.com).
2.  Get the **Transaction Pooler** connection string.
3.  Update `ASYNC_DATABASE_URL` in `server/.env` with the `postgresql+asyncpg://` prefix.

## 4. WhatsApp Pilot (Evolution API)
1.  Launch the stack: `docker-compose -f docker-compose.evolution.yml up -d`.
2.  Open Evolution Dashboard (usually `http://localhost:8080`).
3.  Create instance `Edward_Pilot` and scan QR.
4.  Update `server/.env` with the `EVOLUTION_API_KEY`.

## 5. During the Meeting (Edward & Marketing)
- **Step 1:** Show the **Infinite Canvas** in the dashboard.
- **Step 2:** Trigger a mock message using `python scripts/demo_simulator.py`.
- **Step 3:** Demonstrate the **Sentinel Shield** by typing a forbidden topic (e.g., medical advice).
- **Step 4:** Show how you can **Edit and Approve** a response before it goes to the customer.
- **Step 5:** Mention the **Privacy-First** architecture powered by your local RTX 3060.
