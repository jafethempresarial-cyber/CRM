import asyncio
import json
from database import AsyncSessionLocal, async_engine, Base
from models import AIConfig, Client, Conversation

async def seed_data():
    # Ensure all tables exist before seeding
    from sqlalchemy.ext.asyncio import create_async_engine as _cae
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[OK] Database tables verified.")

    async with AsyncSessionLocal() as db:
        from sqlalchemy import select
        
        # 1. AI Config
        res = await db.execute(select(AIConfig).filter(AIConfig.is_active == True))
        config = res.scalars().first()
        if not config:
            print("Seeding default AI Config...")
            new_config = AIConfig(
                business_name="Jostin AI",
                business_description="Sistema de Ventas Inteligente",
                tone="Professional",
                rules_json=json.dumps(["Be helpful", "Use professional tone"]),
                forbidden_topics_json=json.dumps(["politics", "religion"]),
                language_code="es-CR",
                is_active=True,
                primary_color="#2563eb",
                ui_density="comfortable"
            )
            db.add(new_config)
            print("[OK] Default config added.")
        else:
            print(f"AI Config already exists: {config.business_name}")

        # 2. Sample Client
        res = await db.execute(select(Client).filter(Client.phone_number == "50612345678"))
        client = res.scalars().first()
        if not client:
            print("Seeding sample client...")
            client = Client(name="Cliente de Prueba", phone_number="50612345678")
            db.add(client)
            await db.flush() # Get ID
            print("[OK] Sample client added.")
        
        # 3. Sample Conversation
        res = await db.execute(select(Conversation).filter(Conversation.client_id == client.id))
        conv = res.scalars().first()
        if not conv:
            print("Seeding sample conversation...")
            conv = Conversation(client_id=client.id, channel="whatsapp", is_active=True)
            db.add(conv)
            print("[OK] Sample conversation added.")

        await db.commit()
        print("Seeding completed.")

if __name__ == "__main__":
    asyncio.run(seed_data())
