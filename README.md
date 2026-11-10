# Orbitask Final

Aplikasi manajemen tugas proyek Cloud Computing yang berfungsi penuh: create, edit, delete, status Kanban, statistik, anggota, deadline, kategori, pencarian, filter, named volume, custom network, dan Jenkinsfile.

## Mac

```bash
cd ~/Downloads/orbitask-final
docker compose down
docker compose up -d --build --force-recreate
open http://localhost:8081/?final=1
```

Jika port 8081 masih dipakai versi lama:

```bash
docker rm -f taskflow-frontend taskflow-backend 2>/dev/null || true
docker compose up -d --build --force-recreate
```

Webhook CI/CD berhasil diuji pada 10 November 2026.
