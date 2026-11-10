import json
import os
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


HOST = "0.0.0.0"
PORT = 5000

DATA_DIRECTORY = os.getenv(
    "DATA_DIRECTORY",
    "/var/lib/backend_data",
)

DATA_FILE = os.path.join(
    DATA_DIRECTORY,
    "tasks.json",
)

VALID_PRIORITIES = {
    "low",
    "medium",
    "high",
}

VALID_STATUSES = {
    "todo",
    "in_progress",
    "completed",
}


def get_current_time():
    """Menghasilkan waktu UTC dalam format ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


def initialize_storage():
    """Membuat direktori dan file penyimpanan jika belum tersedia."""
    os.makedirs(DATA_DIRECTORY, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as file:
            json.dump([], file, ensure_ascii=False, indent=2)


def read_tasks():
    """Membaca seluruh data tugas dari tasks.json."""
    initialize_storage()

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except (OSError, json.JSONDecodeError):
        return []


def write_tasks(tasks):
    """Menyimpan data tugas secara aman menggunakan file sementara."""
    initialize_storage()

    temporary_file = f"{DATA_FILE}.tmp"

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(
            tasks,
            file,
            ensure_ascii=False,
            indent=2,
        )

    os.replace(temporary_file, DATA_FILE)


def normalize_task(request_data, existing_task=None):
    """Memvalidasi dan merapikan struktur data tugas."""
    existing_task = existing_task or {}

    title = str(
        request_data.get(
            "title",
            request_data.get(
                "task",
                existing_task.get(
                    "title",
                    existing_task.get("task", ""),
                ),
            ),
        )
    ).strip()

    description = str(
        request_data.get(
            "description",
            existing_task.get("description", ""),
        )
    ).strip()

    member = str(
        request_data.get(
            "member",
            existing_task.get("member", ""),
        )
    ).strip()

    deadline = str(
        request_data.get(
            "deadline",
            existing_task.get("deadline", ""),
        )
    ).strip()

    category = str(
        request_data.get(
            "category",
            existing_task.get("category", "Lainnya"),
        )
    ).strip()

    priority = str(
        request_data.get(
            "priority",
            existing_task.get("priority", "medium"),
        )
    ).lower()

    status = str(
        request_data.get(
            "status",
            existing_task.get("status", "todo"),
        )
    ).lower()

    if not title:
        raise ValueError("Judul tugas wajib diisi")

    if not member:
        raise ValueError("Penanggung jawab wajib diisi")

    if not deadline:
        raise ValueError("Deadline wajib diisi")

    try:
        datetime.strptime(deadline, "%Y-%m-%d")
    except ValueError as error:
        raise ValueError(
            "Format deadline harus YYYY-MM-DD"
        ) from error

    if priority not in VALID_PRIORITIES:
        raise ValueError(
            "Prioritas harus low, medium, atau high"
        )

    if status not in VALID_STATUSES:
        raise ValueError(
            "Status harus todo, in_progress, atau completed"
        )

    return {
        "id": existing_task.get("id")
        or f"task-{uuid.uuid4().hex[:10]}",
        "title": title[:120],
        "task": title[:120],
        "description": description[:500],
        "member": member[:60],
        "category": category[:40],
        "priority": priority,
        "status": status,
        "deadline": deadline,
        "created_at": existing_task.get("created_at")
        or get_current_time(),
        "updated_at": get_current_time(),
    }


class TaskAPIHandler(BaseHTTPRequestHandler):
    """HTTP handler untuk Cloud Task REST API."""

    server_version = "CloudTaskAPI/1.0"

    def send_json_response(self, status_code, payload):
        """Mengirim response dalam format JSON."""
        response = json.dumps(
            payload,
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status_code)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8",
        )

        self.send_header(
            "Content-Length",
            str(len(response)),
        )

        self.send_header(
            "Cache-Control",
            "no-store",
        )

        self.end_headers()
        self.wfile.write(response)

    def read_json_body(self):
        """Membaca dan memvalidasi request body JSON."""
        try:
            content_length = int(
                self.headers.get("Content-Length", "0")
            )
        except ValueError as error:
            raise ValueError(
                "Content-Length tidak valid"
            ) from error

        if content_length < 1:
            raise ValueError("Request body tidak boleh kosong")

        if content_length > 200_000:
            raise ValueError("Request body terlalu besar")

        request_body = self.rfile.read(content_length)

        try:
            return json.loads(
                request_body.decode("utf-8")
            )

        except (
            json.JSONDecodeError,
            UnicodeDecodeError,
        ) as error:
            raise ValueError(
                "Format JSON tidak valid"
            ) from error

    def find_task_index(self, tasks, query):
        """Mencari indeks tugas menggunakan ID atau index."""
        task_id = query.get("id", [""])[0]

        if task_id:
            return next(
                (
                    index
                    for index, task in enumerate(tasks)
                    if task.get("id") == task_id
                ),
                -1,
            )

        try:
            return int(
                query.get("index", ["-1"])[0]
            )

        except ValueError:
            return -1

    def do_GET(self):
        """Menangani request GET."""
        parsed_url = urlparse(self.path)

        if parsed_url.path == "/health":
            initialize_storage()

            storage_writable = os.access(
                DATA_DIRECTORY,
                os.W_OK,
            )

            self.send_json_response(
                200,
                {
                    "status": "healthy",
                    "service": "cloud-task-api",
                    "storage": (
                        "writable"
                        if storage_writable
                        else "readonly"
                    ),
                    "checked_at": get_current_time(),
                },
            )
            return

        if parsed_url.path == "/tasks":
            tasks = read_tasks()
            data_changed = False

            for task in tasks:
                if "title" not in task:
                    task["title"] = task.get(
                        "task",
                        "Tanpa judul",
                    )
                    data_changed = True

                if "task" not in task:
                    task["task"] = task.get(
                        "title",
                        "Tanpa judul",
                    )
                    data_changed = True

                if "status" not in task:
                    task["status"] = "todo"
                    data_changed = True

                if "category" not in task:
                    task["category"] = "Lainnya"
                    data_changed = True

                if "description" not in task:
                    task["description"] = ""
                    data_changed = True

                if "priority" not in task:
                    task["priority"] = "medium"
                    data_changed = True

                if "created_at" not in task:
                    task["created_at"] = get_current_time()
                    data_changed = True

                if "updated_at" not in task:
                    task["updated_at"] = task.get(
                        "created_at",
                        get_current_time(),
                    )
                    data_changed = True

            if data_changed:
                write_tasks(tasks)

            self.send_json_response(
                200,
                {
                    "status": "success",
                    "count": len(tasks),
                    "data": tasks,
                },
            )
            return

        if parsed_url.path == "/stats":
            tasks = read_tasks()

            todo_count = sum(
                1
                for task in tasks
                if task.get("status", "todo") == "todo"
            )

            in_progress_count = sum(
                1
                for task in tasks
                if task.get("status") == "in_progress"
            )

            completed_count = sum(
                1
                for task in tasks
                if task.get("status") == "completed"
            )

            member_statistics = {}

            for task in tasks:
                member_name = task.get(
                    "member",
                    "Tidak ditentukan",
                )

                if member_name not in member_statistics:
                    member_statistics[member_name] = {
                        "total": 0,
                        "todo": 0,
                        "in_progress": 0,
                        "completed": 0,
                    }

                member_statistics[member_name]["total"] += 1

                task_status = task.get(
                    "status",
                    "todo",
                )

                if task_status in VALID_STATUSES:
                    member_statistics[
                        member_name
                    ][task_status] += 1

            self.send_json_response(
                200,
                {
                    "status": "success",
                    "data": {
                        "total": len(tasks),
                        "todo": todo_count,
                        "in_progress": in_progress_count,
                        "completed": completed_count,
                        "members": member_statistics,
                    },
                },
            )
            return

        self.send_json_response(
            404,
            {
                "status": "error",
                "message": "Endpoint tidak ditemukan",
            },
        )

    def do_POST(self):
        """Menangani penambahan tugas."""
        parsed_url = urlparse(self.path)

        if parsed_url.path != "/tasks":
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Endpoint tidak ditemukan",
                },
            )
            return

        try:
            request_data = self.read_json_body()
            new_task = normalize_task(request_data)

            tasks = read_tasks()
            tasks.append(new_task)

            write_tasks(tasks)

            self.send_json_response(
                201,
                {
                    "status": "success",
                    "message": "Tugas berhasil dibuat",
                    "data": new_task,
                },
            )

        except ValueError as error:
            self.send_json_response(
                400,
                {
                    "status": "error",
                    "message": str(error),
                },
            )

        except OSError:
            self.send_json_response(
                500,
                {
                    "status": "error",
                    "message": "Gagal menyimpan data tugas",
                },
            )

    def do_PUT(self):
        """Menangani pembaruan seluruh informasi tugas."""
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        if parsed_url.path != "/tasks":
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Endpoint tidak ditemukan",
                },
            )
            return

        tasks = read_tasks()
        task_index = self.find_task_index(
            tasks,
            query,
        )

        if (
            task_index < 0
            or task_index >= len(tasks)
        ):
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Tugas tidak ditemukan",
                },
            )
            return

        try:
            request_data = self.read_json_body()

            tasks[task_index] = normalize_task(
                request_data,
                tasks[task_index],
            )

            write_tasks(tasks)

            self.send_json_response(
                200,
                {
                    "status": "success",
                    "message": "Tugas berhasil diperbarui",
                    "data": tasks[task_index],
                },
            )

        except ValueError as error:
            self.send_json_response(
                400,
                {
                    "status": "error",
                    "message": str(error),
                },
            )

        except OSError:
            self.send_json_response(
                500,
                {
                    "status": "error",
                    "message": "Gagal memperbarui tugas",
                },
            )

    def do_PATCH(self):
        """Menangani perubahan status tugas."""
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        if parsed_url.path != "/tasks/status":
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Endpoint tidak ditemukan",
                },
            )
            return

        tasks = read_tasks()
        task_index = self.find_task_index(
            tasks,
            query,
        )

        if (
            task_index < 0
            or task_index >= len(tasks)
        ):
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Tugas tidak ditemukan",
                },
            )
            return

        try:
            request_data = self.read_json_body()

            new_status = str(
                request_data.get("status", "")
            ).lower()

            if new_status not in VALID_STATUSES:
                raise ValueError(
                    "Status harus todo, in_progress, "
                    "atau completed"
                )

            tasks[task_index]["status"] = new_status

            tasks[task_index][
                "updated_at"
            ] = get_current_time()

            write_tasks(tasks)

            self.send_json_response(
                200,
                {
                    "status": "success",
                    "message": "Status tugas diperbarui",
                    "data": tasks[task_index],
                },
            )

        except ValueError as error:
            self.send_json_response(
                400,
                {
                    "status": "error",
                    "message": str(error),
                },
            )

        except OSError:
            self.send_json_response(
                500,
                {
                    "status": "error",
                    "message": "Gagal memperbarui status",
                },
            )

    def do_DELETE(self):
        """Menangani penghapusan tugas."""
        parsed_url = urlparse(self.path)
        query = parse_qs(parsed_url.query)

        if parsed_url.path != "/tasks":
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Endpoint tidak ditemukan",
                },
            )
            return

        tasks = read_tasks()
        task_index = self.find_task_index(
            tasks,
            query,
        )

        if (
            task_index < 0
            or task_index >= len(tasks)
        ):
            self.send_json_response(
                404,
                {
                    "status": "error",
                    "message": "Tugas tidak ditemukan",
                },
            )
            return

        try:
            deleted_task = tasks.pop(task_index)
            write_tasks(tasks)

            self.send_json_response(
                200,
                {
                    "status": "success",
                    "message": "Tugas dihapus permanen",
                    "data": deleted_task,
                },
            )

        except OSError:
            self.send_json_response(
                500,
                {
                    "status": "error",
                    "message": "Gagal menghapus tugas",
                },
            )

    def log_message(self, log_format, *args):
        """Menampilkan log request dengan nama aplikasi final."""
        print(
            "[Cloud Task API]",
            log_format % args,
        )


if __name__ == "__main__":
    initialize_storage()

    server = ThreadingHTTPServer(
        (HOST, PORT),
        TaskAPIHandler,
    )

    print(
        f"Cloud Task API berjalan pada "
        f"http://{HOST}:{PORT}"
    )

    try:
        server.serve_forever()

    except KeyboardInterrupt:
        print(
            "\nCloud Task API dihentikan."
        )

    finally:
        server.server_close()
