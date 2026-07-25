"""
seed.py - Mengisi database 'tokokita' dengan data contoh.

Prasyarat:
    pip install pymongo faker
Jalankan:
    python seed.py
"""

import random
from datetime import datetime, timedelta

from pymongo import MongoClient
from faker import Faker

MONGO_URI = "mongodb://localhost:27017"  # koneksi melalui router mongos
JUMLAH_PELANGGAN = 200
JUMLAH_PRODUK = 500
JUMLAH_PESANAN = 5000

fake = Faker("id_ID")
client = MongoClient(MONGO_URI)
db = client["tokokita"]

KATEGORI = ["Elektronik", "Fashion", "Rumah Tangga", "Olahraga",
            "Kecantikan", "Buku", "Mainan", "Makanan"]
STATUS = ["pending", "dibayar", "dikirim", "selesai", "dibatalkan"]


def seed_customers():
    db.customers.drop()
    docs = []
    for i in range(1, JUMLAH_PELANGGAN + 1):
        docs.append({
            "_id": f"CUST-{i:05d}",
            "nama": fake.name(),
            "email": fake.unique.email(),
            "telepon": fake.phone_number(),
            "alamat": {
                "jalan": fake.street_address(),
                "kota": fake.city(),
                "provinsi": fake.state(),
                "kode_pos": fake.postcode(),
            },
            "terdaftar_pada": fake.date_time_between("-2y", "now"),
        })
    db.customers.insert_many(docs)
    print(f"[OK] {len(docs)} pelanggan dimasukkan")


def seed_products():
    db.products.drop()
    docs = []
    for i in range(1, JUMLAH_PRODUK + 1):
        harga = random.randint(10, 5000) * 1000
        docs.append({
            "_id": f"PROD-{i:05d}",
            "nama": fake.catch_phrase(),
            "kategori": random.choice(KATEGORI),
            "harga": harga,
            "stok": random.randint(0, 500),
            "rating": round(random.uniform(3.0, 5.0), 1),
        })
    db.products.insert_many(docs)
    print(f"[OK] {len(docs)} produk dimasukkan")


def seed_orders():
    db.orders.drop()
    produk = list(db.products.find({}, {"harga": 1}))
    docs = []
    for i in range(1, JUMLAH_PESANAN + 1):
        n_item = random.randint(1, 5)
        items, total = [], 0
        for p in random.sample(produk, n_item):
            qty = random.randint(1, 3)
            subtotal = p["harga"] * qty
            total += subtotal
            items.append({"product_id": p["_id"], "qty": qty,
                          "harga_satuan": p["harga"], "subtotal": subtotal})
        tanggal = datetime.now() - timedelta(days=random.randint(0, 365))
        docs.append({
            "_id": f"ORD-{i:07d}",
            "customer_id": f"CUST-{random.randint(1, JUMLAH_PELANGGAN):05d}",
            "tanggal": tanggal,
            "status": random.choice(STATUS),
            "items": items,
            "total": total,
        })
        if len(docs) == 1000:
            db.orders.insert_many(docs)
            docs = []
    if docs:
        db.orders.insert_many(docs)
    print(f"[OK] {JUMLAH_PESANAN} pesanan dimasukkan")


def buat_index():
    db.orders.create_index([("tanggal", -1)])
    db.orders.create_index([("status", 1)])
    db.products.create_index([("kategori", 1), ("harga", 1)])
    print("[OK] Index sekunder dibuat")


if __name__ == "__main__":
    seed_customers()
    seed_products()
    seed_orders()
    buat_index()
    print("\nSelesai. Cek distribusi chunk dengan: "
          "docker exec -it mongos mongosh --eval 'sh.status()'")
