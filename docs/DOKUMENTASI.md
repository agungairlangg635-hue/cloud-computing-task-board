# Dokumentasi Pengujian

Dokumen ini merangkum bukti pengujian aplikasi Cloud Computing Task Board.

## 1. Tampilan dan Pembagian Tugas

- `01-task-board.png`: papan Kanban berisi sembilan tugas.
- `02-team-members.png`: tiga anggota kelompok beserta jumlah tugas.

## 2. Docker dan API

- `03-docker-compose-and-api.png`: backend healthy, frontend pada port 8081, dan respons API.
- `04-volume-inspect.png`: named volume `team-task-data`.
- `05-network-inspect.png`: custom bridge network `app-net` dan kedua container.

## 3. Persistent Storage

- `06-persistence-before.png`: data sebelum backend dihapus.
- `07-backend-removed.png`: container backend berhasil dihapus.
- `08-persistence-after.png`: backend dibuat ulang dan data tetap tersedia.

## 4. Repository dan API

- `09-github-repository.png`: struktur repository GitHub.
- `10-api-testing.png`: GET, POST, DELETE, health check, dan 404.

## 5. Jenkins dan GitHub Webhook

- `11-jenkins-environment-check.png`: Git, Python, Docker CLI, Docker Compose, dan Docker Engine tersedia bagi Jenkins.
- `12-jenkins-manual-build.png`: build manual `#1` sukses.
- `13-jenkins-manual-pipeline.png`: seluruh stage build manual hijau.
- `14-ngrok-online.png`: tunnel HTTPS menuju Jenkins lokal.
- `15-github-webhook-initial.png`: delivery ping awal berhasil.
- `16-jenkins-webhook-build.png`: build otomatis dari GitHub push.
- `17-backend-service-updated.png`: health check final menggunakan `cloud-task-api`, data tetap sembilan, commit dan push berhasil.
- `18-final-webhook-build.png`: build final `#4` dipicu GitHub push.
- `19-final-pipeline-overview.png`: seluruh stage pipeline final hijau.
- `20-final-webhook-deliveries.png`: ping dan dua event push berstatus hijau.

## Kesimpulan

Pengujian membuktikan bahwa aplikasi berjalan pada dua container, data bertahan pada named volume, frontend dan backend terhubung melalui custom network, serta deployment dapat berjalan otomatis dari GitHub push hingga health check Jenkins.
