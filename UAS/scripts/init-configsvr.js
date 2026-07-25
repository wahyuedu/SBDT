// Dijalankan di dalam kontainer cfgsvr1:
//   docker exec -it cfgsvr1 mongosh --file /scripts/init-configsvr.js
// atau salin-tempel isinya ke mongosh.

rs.initiate({
  _id: "cfgrs",
  configsvr: true,
  members: [
    { _id: 0, host: "cfgsvr1:27017" },
    { _id: 1, host: "cfgsvr2:27017" },
    { _id: 2, host: "cfgsvr3:27017" }
  ]
});

// Tunggu hingga PRIMARY terpilih, lalu cek status:
// rs.status()
