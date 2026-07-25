// Dijalankan di mongos SETELAH semua replica set aktif:
//   docker exec -it mongos mongosh --file /scripts/init-router.js

// 1. Daftarkan kedua shard ke cluster
sh.addShard("shard1rs/shard1a:27017,shard1b:27017,shard1c:27017");
sh.addShard("shard2rs/shard2a:27017,shard2b:27017,shard2c:27017");

// 2. Aktifkan sharding pada database e-commerce
sh.enableSharding("tokokita");

// 3. Tentukan shard key per koleksi
//    - orders  : hashed pada customer_id -> distribusi merata,
//                dan semua pesanan satu pelanggan berada di shard yang sama
//    - products: hashed pada _id -> distribusi merata untuk katalog besar
sh.shardCollection("tokokita.orders",   { customer_id: "hashed" });
sh.shardCollection("tokokita.products", { _id: "hashed" });

// Koleksi 'customers' sengaja TIDAK di-shard (unsharded, tinggal di
// primary shard) karena ukurannya relatif kecil dan sering di-join
// (lookup) — ini keputusan desain yang dibahas di dokumentasi.

// 4. Verifikasi
sh.status();
