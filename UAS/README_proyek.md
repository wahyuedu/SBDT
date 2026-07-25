# Sistem Basis Data Terdistribusi (SBDT): E-Commerce TokoKita

Sistem basis data terdistribusi untuk platform e-commerce **TokoKita** menggunakan **MongoDB Sharded Cluster** berisi **10 node**: 1 Config Server Replica Set (3 node), 2 Shard yang masing-masing berupa Replica Set (3 node), dan 1 Router `mongos`. Seluruh node berjalan sebagai kontainer di dalam Docker virtual network.

---

## 👨‍🎓 Informasi Mahasiswa

- **Nama**: Wahyu
- **NIM**: 20220801523
- **Program Studi**: Teknik Informatika
- **Fakultas**: Ilmu Komputer
- **Perguruan Tinggi**: Universitas Esa Unggul

---

## 💡 Konsep SBDT yang Diimplementasikan

| Konsep SBDT | Implementasi pada Sistem TokoKita |
| --- | --- |
| **Fragmentasi Horizontal (Sharding)** | Koleksi `orders` dan `products` dipecah menjadi chunk dan disebar ke `shard1rs` & `shard2rs` berdasarkan shard key, diseimbangkan otomatis oleh *balancer*. |
| **Replikasi (Replica Set)** | Setiap shard dan config server berupa replica set 3 node: 1 PRIMARY (tulis) + 2 SECONDARY (salinan via *oplog*). |
| **Transparansi Lokasi** | Aplikasi hanya terhubung ke router `mongos` pada port 27017 tanpa perlu tahu dokumen tersimpan di shard mana. |
| **Query Tertarget (Targeted Query)** | Shard key `hashed(customer_id)` membuat kueri riwayat pesanan satu pelanggan hanya dieksekusi pada 1 shard, bukan broadcast. |
| **Fault Tolerance & Failover** | Kegagalan node PRIMARY memicu *election* berbasis konsensus Raft; PRIMARY baru terpilih dalam ±5–12 detik tanpa intervensi operator. |
| **Konsistensi Transaksi (ACID)** | Proses checkout mengikat pengurangan stok dan pembuatan pesanan dalam satu transaksi multi-dokumen dengan *rollback* otomatis. |
| **Teorema CAP (CP)** | Saat partisi jaringan sistem memprioritaskan konsistensi; `readPreference=secondaryPreferred` dipakai khusus beban analitik. |

---

## 🏗️ Arsitektur Sistem

```
                        Aplikasi (pymongo)
                               |
                     mongos (router) :27017
                     satu-satunya titik kontak
                               |
        +----------------------+----------------------+
        |                      |                      |
+-------------------+  +-------------------+  +-------------------+
|  CONFIG SERVER RS |  |   SHARD 1 (rs)    |  |   SHARD 2 (rs)    |
|      cfgrs        |  |    shard1rs       |  |    shard2rs       |
|  cfgsvr1 (P)      |  |  shard1a (P)      |  |  shard2a (P)      |
|  cfgsvr2 (S)      |  |  shard1b (S)      |  |  shard2b (S)      |
|  cfgsvr3 (S)      |  |  shard1c (S)      |  |  shard2c (S)      |
| Metadata & chunk  |  |  Chunk subset A   |  |  Chunk subset B   |
+-------------------+  +-------------------+  +-------------------+

P = PRIMARY (menerima tulis)   S = SECONDARY (replika / kandidat failover)
```

**Shard key yang digunakan:**

| Koleksi | Shard Key | Alasan |
| --- | --- | --- |
| `orders` | `{ customer_id: "hashed" }` | Distribusi merata + seluruh pesanan satu pelanggan berada di shard yang sama (query tertarget). |
| `products` | `{ _id: "hashed" }` | Distribusi merata untuk katalog berukuran besar. |
| `customers` | *unsharded* | Koleksi kecil dan sering menjadi acuan `$lookup`, tetap di primary shard. |

---

## 📁 Struktur Direktori

```
UAS-20220801523/
├── README.md                           # Dokumentasi utama proyek
├── Laporan_SBDT.docx                   # Laporan lengkap Tugas Akhir (Word)
├── presentasi_SBDT.pptx                # Slide presentasi (PowerPoint)
├── img/                                # Tangkapan layar & diagram pengujian
│   ├── sh_status.png
│   ├── distribusi_shard.png
│   ├── explain_targeted.png
│   ├── failover_election.png
│   └── transaksi_rollback.png
└── src/                                # Source Code Utama
    ├── docker-compose.yml              # Definisi 10 node kluster MongoDB
    ├── requirements.txt                # Dependensi Python (pymongo, faker)
    ├── simulate.py                     # Skrip otomatisasi setup, seed & uji
    ├── scripts/                        # Skrip inisialisasi kluster
    │   ├── init-configsvr.js           # Inisialisasi config server replica set
    │   ├── init-shards.js              # Inisialisasi replica set shard 1 & 2
    │   └── init-router.js              # addShard + enableSharding + shard key
    ├── app/
    │   ├── seed.py                     # Pengisi data sintetis (200/500/5.000)
    │   └── app.py                      # Demo CRUD, agregasi, read preference, transaksi
    └── tests/
        └── test_cluster.py             # Uji distribusi chunk & panduan failover
```

---

## 🚀 Cara Menjalankan Proyek

### Prasyarat

- Docker Desktop & Docker Compose
- Python 3.9+

### Langkah-Langkah Menjalankan (Docker)

1. Masuk ke direktori `src`:

```bash
cd UAS-20220801523/src
```

2. Pasang dependensi Python:

```bash
pip install -r requirements.txt
```

3. Jalankan seluruh service kluster database (10 kontainer):

```bash
docker compose up -d
```

4. Inisialisasi replica set, sharding, lalu isi data uji:

```bash
python3 simulate.py setup     # init config server, shard, router, shard key
python3 simulate.py seed      # 200 pelanggan, 500 produk, 5.000 pesanan
```

5. Jalankan demo operasi & pengujian:

```bash
python3 simulate.py demo      # CRUD, targeted vs broadcast, agregasi, transaksi
python3 simulate.py test      # distribusi data antar shard
python3 simulate.py status    # ringkasan status kluster
```

6. Akses langsung ke kluster (opsional):

- **Router mongos**: `mongodb://localhost:27017`
- **Shell**: `docker exec -it mongos mongosh`
- **Cek sharding**: `docker exec -it mongos mongosh --eval "sh.status()"`

### Menghentikan & Membersihkan

```bash
docker compose down -v        # hapus kontainer beserta volume data
```

---

## 🖼️ Tangkapan Layar Sistem

### 1. Status Sharded Cluster (`sh.status()`)

![Status Cluster](img/sh_status.png)

### 2. Distribusi Dokumen Antar Shard

![Distribusi Shard](img/distribusi_shard.png)

### 3. Failover Otomatis & Pemilihan PRIMARY Baru

![Failover](img/failover_election.png)

---

## 📊 Skenario Pengujian SBDT

| No | Skenario | Cara Uji | Hasil yang Diharapkan |
| --- | --- | --- | --- |
| **U-1** | Distribusi data antar shard | `$shardedDataDistribution` setelah seeding | `orders` & `products` terbagi ≈50:50 antara kedua shard |
| **U-2** | Query tertarget vs broadcast | `explain()` dengan & tanpa shard key | By `customer_id` → 1 shard; by `status` → semua shard |
| **U-3** | Failover otomatis | `docker stop shard1a` | PRIMARY baru terpilih ±5–12 detik; aplikasi tetap jalan |
| **U-4** | Pemulihan node | `docker start shard1a` | Node kembali sebagai SECONDARY, sinkron via oplog |
| **U-5** | Atomisitas checkout | Transaksi dengan qty melebihi stok | Rollback otomatis; stok & pesanan tidak berubah |

### Cara Menjalankan Uji Failover (U-3 & U-4)

```bash
# 1. Matikan node PRIMARY shard 1
docker stop shard1a

# 2. Amati pemilihan PRIMARY baru (±5-12 detik)
docker exec -it shard1b mongosh --eval \
  'rs.status().members.forEach(m => print(m.name, m.stateStr))'

# 3. Aplikasi tetap berfungsi tanpa perubahan kode
python3 simulate.py demo

# 4. Hidupkan kembali node -> bergabung sebagai SECONDARY
docker start shard1a
```

---

## 🧩 Pemetaan Kebutuhan Sistem

| Kode | Kebutuhan | Solusi Arsitektur |
| --- | --- | --- |
| **K-01** | Data pesanan melebihi kapasitas satu server | Sharding koleksi `orders` ke 2 shard (dapat ditambah tanpa henti layanan) |
| **K-02** | Layanan tetap hidup saat satu server mati | Setiap shard = replica set 3 node dengan failover otomatis |
| **K-03** | Riwayat pesanan per pelanggan cepat diakses | Shard key `hashed(customer_id)` → query tertarget ke 1 shard |
| **K-04** | Checkout mengubah stok + membuat pesanan atomik | Transaksi multi-dokumen ACID lintas koleksi |
| **K-05** | Laporan penjualan tidak mengganggu operasi utama | `readPreference=secondaryPreferred` untuk beban analitik |

---

## 🛠️ Teknologi yang Digunakan

- **MongoDB 7.0** — image resmi Docker (`mongo:7.0`)
- **Docker & Docker Compose** — orkestrasi 10 kontainer dalam satu virtual network
- **Python 3** — `pymongo` (driver resmi) & `faker` (pembangkit data sintetis berlokal `id_ID`)

---

© 2026 Wahyu (20220801523) - Universitas Esa Unggul.
