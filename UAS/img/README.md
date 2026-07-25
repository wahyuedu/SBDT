# Tangkapan Layar Pengujian

Letakkan tangkapan layar hasil pengujian pada folder ini dengan nama berikut agar
otomatis tampil pada README utama:

| Berkas | Isi yang disarankan |
| --- | --- |
| `sh_status.png` | Keluaran `sh.status()` yang menampilkan kedua shard terdaftar |
| `distribusi_shard.png` | Keluaran `$shardedDataDistribution` (jumlah dokumen per shard) |
| `explain_targeted.png` | Perbandingan `explain()` query tertarget vs broadcast |
| `failover_election.png` | Keluaran `rs.status()` saat PRIMARY baru terpilih |
| `transaksi_rollback.png` | Bukti rollback transaksi saat stok tidak mencukupi |
