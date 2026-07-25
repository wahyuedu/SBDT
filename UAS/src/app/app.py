"""
app.py - Demo operasi pada database terdistribusi TokoKita.

Mendemonstrasikan:
1. CRUD dasar melalui mongos
2. Query tertarget (targeted) vs broadcast (scatter-gather)
3. Agregasi terdistribusi (laporan penjualan)
4. Read preference (membaca dari secondary)
5. Transaksi multi-dokumen (checkout: kurangi stok + buat pesanan)

Jalankan: python app.py
"""

from datetime import datetime

from pymongo import MongoClient, ReadPreference
from pymongo.errors import PyMongoError

client = MongoClient("mongodb://localhost:27017")
db = client["tokokita"]


def demo_crud():
    print("\n=== 1. CRUD Dasar ===")
    # CREATE
    db.products.insert_one({
        "_id": "PROD-99999", "nama": "Demo Keyboard Mekanik",
        "kategori": "Elektronik", "harga": 750000, "stok": 25, "rating": 4.8,
    })
    # READ
    p = db.products.find_one({"_id": "PROD-99999"})
    print("Produk dibuat:", p["nama"], "-", p["harga"])
    # UPDATE
    db.products.update_one({"_id": "PROD-99999"}, {"$inc": {"stok": -1}})
    # DELETE
    db.products.delete_one({"_id": "PROD-99999"})
    print("CRUD selesai (create -> read -> update -> delete)")


def demo_targeted_vs_broadcast():
    print("\n=== 2. Targeted vs Broadcast Query ===")
    # Targeted: filter memuat shard key (customer_id) -> hanya 1 shard disentuh
    plan = db.orders.find({"customer_id": "CUST-00001"}).explain()
    shards = list(plan["queryPlanner"].get("winningPlan", {})
                  .get("shards", []))
    print(f"Query by customer_id  -> shard yang dieksekusi: "
          f"{[s['shardName'] for s in shards] or 'lihat explain'}")

    # Broadcast: filter TANPA shard key -> semua shard disentuh
    plan2 = db.orders.find({"status": "dikirim"}).explain()
    shards2 = list(plan2["queryPlanner"].get("winningPlan", {})
                   .get("shards", []))
    print(f"Query by status       -> shard yang dieksekusi: "
          f"{[s['shardName'] for s in shards2] or 'lihat explain'}")


def demo_agregasi():
    print("\n=== 3. Agregasi Terdistribusi: Penjualan per Kategori ===")
    pipeline = [
        {"$match": {"status": {"$in": ["dibayar", "dikirim", "selesai"]}}},
        {"$unwind": "$items"},
        {"$lookup": {
            "from": "products", "localField": "items.product_id",
            "foreignField": "_id", "as": "produk"}},
        {"$unwind": "$produk"},
        {"$group": {
            "_id": "$produk.kategori",
            "omzet": {"$sum": "$items.subtotal"},
            "jumlah_transaksi": {"$sum": 1}}},
        {"$sort": {"omzet": -1}},
        {"$limit": 5},
    ]
    for row in db.orders.aggregate(pipeline):
        print(f"  {row['_id']:<15} omzet=Rp{row['omzet']:>15,} "
              f"({row['jumlah_transaksi']} item terjual)")


def demo_read_preference():
    print("\n=== 4. Read Preference: SECONDARY_PREFERRED ===")
    db_sec = client.get_database(
        "tokokita", read_preference=ReadPreference.SECONDARY_PREFERRED)
    n = db_sec.orders.count_documents({})
    print(f"Total pesanan (dibaca dari secondary bila tersedia): {n}")


def demo_transaksi():
    print("\n=== 5. Transaksi Multi-Dokumen: Checkout ===")
    produk_id, qty, cust = "PROD-00001", 2, "CUST-00001"
    with client.start_session() as session:
        try:
            with session.start_transaction():
                p = db.products.find_one_and_update(
                    {"_id": produk_id, "stok": {"$gte": qty}},
                    {"$inc": {"stok": -qty}},
                    session=session,
                )
                if p is None:
                    raise ValueError("Stok tidak mencukupi")
                db.orders.insert_one({
                    "_id": f"ORD-TX-{datetime.now():%Y%m%d%H%M%S}",
                    "customer_id": cust,
                    "tanggal": datetime.now(),
                    "status": "dibayar",
                    "items": [{
                        "product_id": produk_id, "qty": qty,
                        "harga_satuan": p["harga"],
                        "subtotal": p["harga"] * qty}],
                    "total": p["harga"] * qty,
                }, session=session)
            print("Transaksi checkout BERHASIL (stok berkurang + pesanan dibuat)")
        except (PyMongoError, ValueError) as e:
            print("Transaksi DIBATALKAN (rollback otomatis):", e)


if __name__ == "__main__":
    demo_crud()
    demo_targeted_vs_broadcast()
    demo_agregasi()
    demo_read_preference()
    demo_transaksi()
