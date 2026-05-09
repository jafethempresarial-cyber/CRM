import pytest
import os
import sys
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add server to path
sys.path.append(os.path.join(os.path.dirname(__file__), '../'))
os.environ["TESTING"] = "true"

from main import app
from database import Base, get_async_db
from models import User, AIConfig, Product, Order
from services.auth_service import AuthService
from services.licensing import LicensingService

# Helper to ensure license keys exist for generation (needed in CI)
def ensure_keys_exist():
    keys_dir = os.path.join(os.path.dirname(__file__), '../keys')
    private_key = os.path.join(keys_dir, 'private.pem')
    public_key = os.path.join(keys_dir, 'public.pem')
    
    if not os.path.exists(private_key):
        print("CI/Test Environment detected: Generating temporary license keys...")
        os.makedirs(keys_dir, exist_ok=True)
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        # Generate new temp key pair
        pk = ed25519.Ed25519PrivateKey.generate()
        
        # Save Private
        with open(private_key, "wb") as f:
            f.write(pk.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
            
        # Save Public
        with open(public_key, "wb") as f:
            f.write(pk.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))

# Test database setup - Use a unique file for this test to avoid shared-memory loop issues
TEST_DB_FILE = "test_ecommerce.db"
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///./{TEST_DB_FILE}"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def override_get_async_db():
    async with TestingSessionLocal() as session:
        yield session

@pytest.fixture(autouse=True)
def setup_db_overrides():
    app.dependency_overrides[get_async_db] = override_get_async_db
    yield
    app.dependency_overrides.clear()

async def init_test_db():
    ensure_keys_exist()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestingSessionLocal() as session:
        # 1. Create Admin User
        admin_user = User(
            username="admin",
            hashed_password=AuthService.get_password_hash("password"),
            role="admin"
        )
        session.add(admin_user)
        
        # 2. Create Enterprise License
        try:
            from generate_license import generate_license
            test_license_data = {
                "business_name": "Test Shop",
                "plan": "enterprise",
                "features": ["whatsapp", "ecommerce"],
                "max_seats": 10
            }
            test_key = generate_license(test_license_data)
        except Exception:
            test_key = "ci-test-license-key"
        
        config = AIConfig(
            business_name="Test Shop",
            is_active=True,
            license_key=test_key
        )
        session.add(config)
        
        # 3. Create a Product
        product = Product(
            id=1,
            name="Test Widget",
            price=1000,
            stock_quantity=50
        )
        session.add(product)
        
        await session.commit()

async def downgrade_license(plan: str):
    async with TestingSessionLocal() as session:
        try:
            from generate_license import generate_license
            test_license_data = {
                "business_name": "Test Shop",
                "plan": plan,
                "features": ["whatsapp"],
                "max_seats": 10
            }
            test_key = generate_license(test_license_data)
        except Exception:
            test_key = f"ci-test-license-{plan}"
        from sqlalchemy import update
        await session.execute(update(AIConfig).where(AIConfig.is_active == True).values(license_key=test_key))
        await session.commit()

@pytest.mark.asyncio
async def test_ecommerce_flow():
    # 1. Initialize DB
    await init_test_db()
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 2. Login
        response = await client.post("/auth/login", data={"username": "admin", "password": "password"})
        if response.status_code != 200:
            print(f"DEBUG: Login Response Status: {response.status_code}")
            print(f"DEBUG: Login Response Content: {response.text}")
        assert response.status_code == 200, f"Login failed: {response.text}"
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. List Products
        response = await client.get("/ecommerce/products")
        assert response.status_code == 200
        products = response.json()
        assert len(products) >= 1
        assert products[0]["name"] == "Test Widget"
        
        # 4. Create Order
        order_data = {
            "client_id": 1,
            "items": [
                {"product_id": 1, "quantity": 2}
            ]
        }
        response = await client.post("/ecommerce/orders", json=order_data, headers=headers)
        if response.status_code != 200:
            print(f"DEBUG: Order Response Status: {response.status_code}")
            print(f"DEBUG: Order Response Content: {response.text}")
        assert response.status_code == 200, f"Order creation failed: {response.text}"
        order = response.json()
        assert order["total_amount"] == 2000
        assert "Test Widget" in order["items_json"]
        
        # 5. Test Plan Restriction
        await downgrade_license("starter")
        response = await client.get("/ecommerce/products")
        assert response.status_code == 403
        assert "enterprise" in response.json()["detail"].lower()

    # Cleanup
    await engine.dispose()
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
