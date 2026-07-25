"""
test_cluster.py - Pengujian cluster terdistribusi.

Uji 1: Distribusi data antar shard (via $shardedDataDistribution)
Uji 2: Konsistensi jumlah dokumen
Uji 3 (manual): Failover - lihat instruksi di bawah / README.

Jalankan: python test_cluster.py
"""

from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017")
db = client["tokokita"]


def uji_distribusi():
    print("=== Uji 1: Distribusi Data per Shard ===")
    admin = client["admin"]
    hasil = admin.aggregate([{"$shardedDataDistribution": {}}])
    for ns in hasil:
        if not ns["ns"].startswith("tokokita."):
            continue
        print(f"\nKoleksi: {ns['ns']}")
        for s in ns["shards"]:
            print(f"  {s['shardName']:<10} "
                  f"dokumen={s['numOwnedDocuments']:>7,}  "
                  f"ukuran={s['ownedSizeBytes']/1024:>10.1f} KB")


def uji_konsistensi():
    print("\n=== Uji 2: Konsistensi Jumlah Dokumen ===")
    for koleksi in ["customers", "products", "orders"]:
        n = db[koleksi].count_documents({})
        print(f"  {koleksi:<10}: {n:,} dokumen")


if __name__ == "__main__":
    uji_distribusi()
    uji_konsistensi()
    print("""
=== Uji 3 (Manual): Failover Replica Set ===
1. Matikan node PRIMARY shard 1:
     docker stop shard1a
2. Dalam ~10 detik replica set memilih PRIMARY baru. Cek:
     docker exec -it shard1b mongosh --eval 'rs.status().members.forEach(m => print(m.name, m.stateStr))'
3. Jalankan kembali `python app.py` -> operasi tetap berhasil
   (bukti high availability tanpa intervensi manual).
4. Hidupkan kembali node:
     docker start shard1a
   Node akan bergabung sebagai SECONDARY dan menyinkronkan data (oplog replay).
""")
