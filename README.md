# Cloud Computing Task Board

Aplikasi pembagian tugas kelompok berbasis web untuk proyek mata kuliah **Cloud Computing**, kelas **47-REG-GAB02**, Telkom University. Studi kasus yang digunakan adalah **Team Task & Note List**.

Aplikasi menjalankan frontend Nginx dan backend Python REST API pada container terpisah. Data disimpan pada Docker named volume, kedua service berkomunikasi melalui custom bridge network, dan deployment diotomatisasi menggunakan Jenkins Pipeline dan GitHub Webhook melalui ngrok.

## Identitas Proyek

- Mata kuliah: Cloud Computing
- Dosen: Favian Dewanta
- Kelas: 47-REG-GAB02
- Semester: 7
- Tahun akademik: 2026
- Deadline: 11 November 2026

## Anggota Kelompok

| Nama                         | NIM           |
| ---------------------------- | ------------- |
| Muhammad Agung Airlangga     | 101012330215  |
| Faurina Anum Az Zahra        | 1010012300034 |
| Irdianta Maheswara Widyatama | 101012300334  |

## Fitur Aplikasi

- Menambahkan, menampilkan, mengedit, dan menghapus tugas
- Memindahkan status tugas: `todo`, `in_progress`, dan `completed`
- Drag-and-drop antarkolom Kanban
- Pencarian dan filter anggota, kategori, serta prioritas
- Deadline dan indikator tugas terlambat
- Ringkasan progres dan pembagian tugas anggota
- Health check backend dan statistik tugas

## Teknologi

- Python 3.12 dan `ThreadingHTTPServer`
- HTML5, CSS3, dan Vanilla JavaScript
- Nginx Alpine
- Docker Desktop dan Docker Compose
- Docker named volume `team-task-data`
- Docker custom bridge network `app-net`
- Jenkins LTS dan Declarative Pipeline
- GitHub, GitHub Webhook, dan ngrok

## Struktur Proyek

```text
cloud-board-final/
├── backend/
│   ├── app.py
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── styles.css
│   ├── app.js
│   └── nginx.conf
├── docs/
│   ├── screenshots/
│   └── DOKUMENTASI.md
├── docker-compose.yml
├── Jenkinsfile
├── README.md
└── .gitignore
```

## Arsitektur

```text
Browser :8081
     |
     v
Frontend Container (Nginx :80)
     |
     | /api melalui Docker DNS: backend
     v
Backend Container (Python REST API :5000)
     |
     v
Named Volume: team-task-data
     |
     v
tasks.json
```

Frontend dan backend berada pada custom bridge network `app-net`.

Alur CI/CD:

```text
git push -> GitHub -> Webhook -> ngrok -> Jenkins
         -> Syntax Check -> Build Image -> Deployment -> Health Check
```

## Menjalankan Aplikasi di macOS

Pastikan Docker Desktop aktif. Karena volume dan network didefinisikan sebagai resource external, buat keduanya jika belum tersedia:

```bash
docker volume inspect team-task-data >/dev/null 2>&1 \
  || docker volume create team-task-data

docker network inspect app-net >/dev/null 2>&1 \
  || docker network create app-net
```

Jalankan aplikasi menggunakan project name yang sama dengan Jenkins:

```bash
docker compose -p taskflow-cloud up -d --build
```

Periksa service:

```bash
docker compose -p taskflow-cloud ps
```

Buka aplikasi:

```text
http://localhost:8081
```

Menghentikan aplikasi tanpa menghapus data:

```bash
docker compose -p taskflow-cloud down
```

> Jangan menggunakan `docker compose down -v` jika data masih ingin dipertahankan.

## Dokumentasi API

Base URL melalui Nginx:

```text
http://localhost:8081/api
```

| Method | Endpoint                       | Fungsi                                                    |
| ------ | ------------------------------ | --------------------------------------------------------- |
| GET    | `/api/health`                  | Health check backend dan storage                          |
| GET    | `/api/tasks`                   | Menampilkan seluruh tugas                                 |
| GET    | `/api/stats`                   | Menampilkan statistik tugas dan anggota                   |
| POST   | `/api/tasks`                   | Menambahkan tugas                                         |
| PUT    | `/api/tasks?id=TASK_ID`        | Memperbarui tugas                                         |
| PATCH  | `/api/tasks/status?id=TASK_ID` | Mengubah status tugas                                     |
| DELETE | `/api/tasks?index=X`           | Menghapus tugas berdasarkan indeks, sesuai endpoint wajib |
| DELETE | `/api/tasks?id=TASK_ID`        | Menghapus tugas berdasarkan ID                            |

Contoh health check:

```bash
curl http://localhost:8081/api/health
```

Contoh menambahkan tugas:

```bash
curl -X POST http://localhost:8081/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Menguji named volume",
    "description": "Memastikan data tetap tersedia setelah container dibuat ulang.",
    "member": "Muhammad Agung Airlangga",
    "deadline": "2026-11-11",
    "category": "Storage",
    "priority": "high",
    "status": "todo"
  }'
```

Contoh endpoint wajib DELETE:

```bash
curl -X DELETE "http://localhost:8081/api/tasks?index=0"
```

## Pengujian Persistent Storage

Named volume:

```text
team-task-data -> /var/lib/backend_data
```

Pengujian dilakukan dengan urutan:

```bash
curl http://localhost:8081/api/tasks
docker rm -f taskflow-backend
docker compose -p taskflow-cloud up -d
curl http://localhost:8081/api/tasks
```

Data tetap berjumlah sembilan setelah container backend dihapus dan dibuat kembali. Hal ini membuktikan bahwa data tersimpan pada named volume, bukan pada writable layer container.

## Jenkins Pipeline

`Jenkinsfile` menjalankan tahap berikut:

1. Checkout
2. Syntax Check
3. Build Image
4. Automated Deployment
5. Health Check

Build manual berhasil dijalankan sebagai build `#1`. Build otomatis dari GitHub Webhook juga berhasil, termasuk build final `#4` setelah nama service backend disesuaikan menjadi `cloud-task-api`.

## GitHub Webhook

Webhook aktif untuk event `push` dengan content type `application/json`. URL publik ngrok meneruskan request menuju Jenkins lokal pada port `8080` dan endpoint `/github-webhook/`.

Bukti akhir menunjukkan delivery `ping` dan dua delivery `push` berstatus hijau. Jenkins menampilkan `Started by GitHub push`, lalu seluruh stage selesai dengan status sukses.

## Pembagian Tugas

| Anggota                      | Tanggung jawab                                                 |
| ---------------------------- | -------------------------------------------------------------- |
| Muhammad Agung Airlangga     | Dokumentasi README, pengujian antarmuka, dan video demonstrasi |
| Faurina Anum Az Zahra        | Frontend, Nginx, dan integrasi frontend dengan API             |
| Irdianta Maheswara Widyatama | Backend Python, Docker, storage, network, Jenkins, dan webhook |

## Dokumentasi Hasil

Dokumentasi lengkap dan caption tersedia pada [docs/DOKUMENTASI.md](docs/DOKUMENTASI.md).

### Tampilan Aplikasi

![Papan tugas](docs/screenshots/01-task-board.png)

![Anggota kelompok](docs/screenshots/02-team-members.png)

### Docker, Storage, dan Network

![Docker Compose dan API](docs/screenshots/03-docker-compose-and-api.png)

![Named volume](docs/screenshots/04-volume-inspect.png)

![Custom network](docs/screenshots/05-network-inspect.png)

### Persistent Storage

![Data sebelum backend dihapus](docs/screenshots/06-persistence-before.png)

![Backend dihapus](docs/screenshots/07-backend-removed.png)

![Data tetap tersedia](docs/screenshots/08-persistence-after.png)

### API dan Repository

![Repository GitHub](docs/screenshots/09-github-repository.png)

![Pengujian API](docs/screenshots/10-api-testing.png)

### Jenkins dan Webhook

![Build manual](docs/screenshots/12-jenkins-manual-build.png)

![Pipeline manual](docs/screenshots/13-jenkins-manual-pipeline.png)

![Build otomatis final](docs/screenshots/18-final-webhook-build.png)

![Pipeline otomatis final](docs/screenshots/19-final-pipeline-overview.png)

![Delivery webhook final](docs/screenshots/20-final-webhook-deliveries.png)

## Keamanan

Repository tidak menyimpan GitHub Personal Access Token, ngrok authtoken, password Jenkins, atau file `.env`.

## Video Demonstrasi

Tautan video 5-8 menit:

```text
MASUKKAN_LINK_VIDEO_DI_SINI
```

Pengujian CI/CD pada video demonstrasi berhasil.
