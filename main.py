import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4

from database import db, create_document, get_documents
from schemas import CharacterModel

app = FastAPI(title="3D Character Shop API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "3D Character Shop API running"}

@app.get("/schema")
def get_schema():
    # Return minimal info about schemas for the viewer
    return {
        "collections": [
            {
                "name": "charactermodel",
                "schema": CharacterModel.model_json_schema(),
            }
        ]
    }

# Seed some demo models if collection empty (helper)
@app.post("/seed")
def seed_demo_models():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    existing = db["charactermodel"].count_documents({})
    if existing > 0:
        return {"seeded": False, "message": "Collection already has documents"}

    demo_items = [
        CharacterModel(
            name="Neon Runner",
            description="Stylized cyberpunk runner with glowing accents",
            price=29.0,
            thumbnail_url="https://images.unsplash.com/photo-1542751371-adc38448a05e?w=800&q=80&auto=format&fit=crop",
            preview_url="https://youtu.be/dQw4w9WgXcQ",
            tags=["cyberpunk", "stylized", "game-ready"],
            formats=["FBX", "GLB"],
            polycount="28k tris",
            rigged=True,
            animated=True,
            rating=4.6,
        ),
        CharacterModel(
            name="Forest Guardian",
            description="Fantasy archer with cloak and light armor",
            price=39.0,
            thumbnail_url="https://images.unsplash.com/photo-1605721911519-3dfeb3be25e7?w=800&q=80&auto=format&fit=crop",
            tags=["fantasy", "archer", "PBR"],
            formats=["FBX", "OBJ"],
            polycount="32k tris",
            rigged=True,
            animated=False,
            rating=4.8,
        ),
        CharacterModel(
            name="Mech Scout",
            description="Compact sci-fi mech with emissive details",
            price=24.0,
            thumbnail_url="https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=800&q=80&auto=format&fit=crop",
            tags=["sci-fi", "mech", "low-poly"],
            formats=["GLB"],
            polycount="18k tris",
            rigged=False,
            animated=False,
            rating=4.2,
        ),
    ]

    for item in demo_items:
        create_document("charactermodel", item)

    return {"seeded": True, "count": len(demo_items)}

# Public endpoints
class ListQuery(BaseModel):
    tag: Optional[str] = None
    q: Optional[str] = None
    limit: int = 50

@app.get("/models")
def list_models(tag: Optional[str] = None, q: Optional[str] = None, limit: int = 50):
    if db is None:
        # allow frontend to still demo without DB
        return []
    filt = {}
    if tag:
        filt["tags"] = {"$in": [tag]}
    if q:
        filt["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
        ]
    docs = get_documents("charactermodel", filt, limit)
    # Convert ObjectId and datetimes
    def convert(doc):
        doc["id"] = str(doc.pop("_id", ""))
        for k in ["created_at", "updated_at"]:
            if k in doc and hasattr(doc[k], "isoformat"):
                doc[k] = doc[k].isoformat()
        return doc
    return [convert(d) for d in docs]

# --- Simple Checkout Endpoint ---
class CheckoutItem(BaseModel):
    id: str
    qty: int

class CheckoutRequest(BaseModel):
    items: List[CheckoutItem]

@app.post("/checkout")
def checkout(payload: CheckoutRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items in checkout")

    # Fetch items and compute totals
    ids = [i.id for i in payload.items]
    qty_map = {i.id: max(1, i.qty) for i in payload.items}

    from bson import ObjectId
    # Collect docs that exist
    found = list(db["charactermodel"].find({"_id": {"$in": [ObjectId(i) for i in ids if ObjectId.is_valid(i)]}}))

    if not found:
        raise HTTPException(status_code=404, detail="Models not found")

    # Update downloads counters
    for doc in found:
        inc = qty_map.get(str(doc["_id"]), 1)
        try:
            db["charactermodel"].update_one({"_id": doc["_id"]}, {"$inc": {"downloads": inc}})
        except Exception:
            pass

    # Build receipt
    line_items = []
    subtotal = 0.0
    for doc in found:
        q = qty_map.get(str(doc["_id"]), 1)
        price = float(doc.get("price", 0))
        total = price * q
        subtotal += total
        line_items.append({
            "id": str(doc["_id"]),
            "name": doc.get("name"),
            "qty": q,
            "price": price,
            "line_total": total,
            "download_links": [
                # In a real app these would be signed URLs
                doc.get("preview_url") or doc.get("thumbnail_url")
            ]
        })

    return {
        "order_id": str(uuid4()),
        "items": line_items,
        "subtotal": subtotal,
        "message": "Order confirmed. Download links are ready.",
    }

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
