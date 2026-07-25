#!/usr/bin/env python3
"""
simulate.py - Skrip otomatisasi setup, seeding, demo, dan pengujian
              kluster MongoDB terdistribusi TokoKita.

Penggunaan:
    python3 simulate.py setup     # inisialisasi replica set + sharding
    python3 simulate.py seed      # isi data sintetis
    python3 simulate.py demo      # jalankan demo operasi terdistribusi
    python3 simulate.py test      # uji distribusi data antar shard
    python3 simulate.py status    # ringkasan status kluster
    python3 simulate.py all       # setup -> seed -> demo -> test
"""

import subprocess
import sys
import time

MONGOS = "mongos"
CFG_PRIMARY = "cfgsvr1"
SHARD1_PRIMARY = "shard1a"
SHARD2_PRIMARY = "shard2a"


# ----------------------------------------------------------------------
# Utilitas
# ----------------------------------------------------------------------
def info(pesan):
    print(f"\n\033[94m[INFO]\033[0m {pesan}")


def ok(pesan):
    print(f"\033[92m[OK]\033[0m   {pesan}")


def gagal(pesan):
    print(f"\033[91m[GAGAL]\033[0m {pesan}")


def mongosh(container, perintah, diamkan_error=False):
    """Menjalankan perintah mongosh di dalam kontainer tertentu."""
    hasil = subprocess.run(
        ["docker", "exec", container, "mongosh", "--quiet", "--eval", perintah],
        capture_output=True, text=True,
    )
    if hasil.returncode != 0 and not diamkan_error:
        gagal(f"{container}: {hasil.stderr.strip()[:200]}")
    return hasil.stdout.strip()


def tunggu(detik, keterangan):
    print(f"       menunggu {detik} detik ({keterangan})...", end="", flush=True)
    time.sleep(detik)
    print(" selesai")


# ----------------------------------------------------------------------
# 1. SETUP
# ----------------------------------------------------------------------
def setup():
    info("Tahap 1/4 - Inisialisasi config server replica set (cfgrs)")
    mongosh(CFG_PRIMARY, """
        rs.initiate({
          _id: "cfgrs", configsvr: true,
          members: [
            { _id: 0, host: "cfgsvr1:27017" },
            { _id: 1, host: "cfgsvr2:27017" },
            { _id: 2, host: "cfgsvr3:27017" }
          ]
        })
    """, diamkan_error=True)
    tunggu(15, "menunggu PRIMARY config server terpilih")
    ok("Config server replica set aktif")

    info("Tahap 2/4 - Inisialisasi replica set shard 1 dan shard 2")
    mongosh(SHARD1_PRIMARY, """
        rs.initiate({
          _id: "shard1rs",
          members: [
            { _id: 0, host: "shard1a:27017", priority: 2 },
            { _id: 1, host: "shard1b:27017" },
            { _id: 2, host: "shard1c:27017" }
          ]
        })
    """, diamkan_error=True)
    mongosh(SHARD2_PRIMARY, """
        rs.initiate({
          _id: "shard2rs",
          members: [
            { _id: 0, host: "shard2a:27017", priority: 2 },
            { _id: 1, host: "shard2b:27017" },
            { _id: 2, host: "shard2c:27017" }
          ]
        })
    """, diamkan_error=True)
    tunggu(20, "menunggu PRIMARY tiap shard terpilih")
    ok("Kedua replica set shard aktif")

    info("Tahap 3/4 - Mendaftarkan shard ke kluster melalui mongos")
    mongosh(MONGOS, 'sh.addShard("shard1rs/shard1a:27017,shard1b:27017,shard1c:27017")')
    mongosh(MONGOS, 'sh.addShard("shard2rs/shard2a:27017,shard2b:27017,shard2c:27017")')
    ok("Shard 1 dan shard 2 terdaftar")

    info("Tahap 4/4 - Mengaktifkan sharding dan menetapkan shard key")
    mongosh(MONGOS, 'sh.enableSharding("tokokita")')
    mongosh(MONGOS, 'sh.shardCollection("tokokita.orders", { customer_id: "hashed" })')
    mongosh(MONGOS, 'sh.shardCollection("tokokita.products", { _id: "hashed" })')
    ok("Sharding aktif: orders -> hashed(customer_id), products -> hashed(_id)")

    print("\nSetup selesai. Lanjutkan dengan: python3 simulate.py seed")


# ----------------------------------------------------------------------
# 2-4. SEED / DEMO / TEST
# ----------------------------------------------------------------------
def jalankan_python(berkas, judul):
    info(judul)
    hasil = subprocess.run([sys.executable, berkas])
    if hasil.returncode == 0:
        ok(f"{berkas} selesai dijalankan")
    else:
        gagal(f"{berkas} berhenti dengan kode {hasil.returncode}")


def seed():
    jalankan_python("app/seed.py", "Mengisi data sintetis ke kluster")


def demo():
    jalankan_python("app/app.py", "Menjalankan demo operasi terdistribusi")


def test():
    jalankan_python("tests/test_cluster.py", "Menjalankan pengujian distribusi data")


# ----------------------------------------------------------------------
# 5. STATUS
# ----------------------------------------------------------------------
def status():
    info("Ringkasan status kluster")

    print("\n--- Daftar shard terdaftar ---")
    print(mongosh(MONGOS, 'db.adminCommand({listShards:1}).shards.forEach('
                          'function(s){ print(s._id + "  ->  " + s.host) })'))

    print("\n--- Status node tiap replica set ---")
    for c, nama in [(SHARD1_PRIMARY, "shard1rs"), (SHARD2_PRIMARY, "shard2rs")]:
        print(f"\n[{nama}]")
        print(mongosh(c, 'rs.status().members.forEach('
                         'function(m){ print("  " + m.name + "  " + m.stateStr) })',
                      diamkan_error=True))

    print("\n--- Jumlah dokumen per koleksi ---")
    print(mongosh(MONGOS, 'db = db.getSiblingDB("tokokita"); '
                          '["customers","products","orders"].forEach('
                          'function(c){ print("  " + c + ": " + db[c].countDocuments({})) })'))


# ----------------------------------------------------------------------
PERINTAH = {
    "setup": setup, "seed": seed, "demo": demo,
    "test": test, "status": status,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in list(PERINTAH) + ["all"]:
        print(__doc__)
        sys.exit(1)

    aksi = sys.argv[1]
    if aksi == "all":
        setup(); seed(); demo(); test()
    else:
        PERINTAH[aksi]()
