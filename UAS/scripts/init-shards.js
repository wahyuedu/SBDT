// ===== SHARD 1 =====
// Jalankan di kontainer shard1a:
//   docker exec -it shard1a mongosh --eval '
rs.initiate({
  _id: "shard1rs",
  members: [
    { _id: 0, host: "shard1a:27017", priority: 2 },  // kandidat utama PRIMARY
    { _id: 1, host: "shard1b:27017", priority: 1 },
    { _id: 2, host: "shard1c:27017", priority: 1 }
  ]
});
// '

// ===== SHARD 2 =====
// Jalankan di kontainer shard2a:
//   docker exec -it shard2a mongosh --eval '
rs.initiate({
  _id: "shard2rs",
  members: [
    { _id: 0, host: "shard2a:27017", priority: 2 },
    { _id: 1, host: "shard2b:27017", priority: 1 },
    { _id: 2, host: "shard2c:27017", priority: 1 }
  ]
});
// '
