const $ = (s) => document.querySelector(s),
  $$ = (s) => [...document.querySelectorAll(s)];
let tasks = [],
  editing = null,
  formStatus = "todo",
  filters = { search: "", member: "all", category: "all", priority: "all" };
const esc = (v) => {
    const d = document.createElement("div");
    d.textContent = v || "";
    return d.innerHTML;
  },
  initials = (n) =>
    (n || "?")
      .trim()
      .split(/\s+/)
      .slice(0, 2)
      .map((x) => x[0])
      .join("")
      .toUpperCase(),
  days = (d) => {
    const t = new Date();
    t.setHours(0, 0, 0, 0);
    return Math.ceil((new Date(d + "T00:00:00") - t) / 864e5);
  },
  fmt = (d) =>
    new Intl.DateTimeFormat("id-ID", {
      day: "numeric",
      month: "short",
      year: "numeric",
    }).format(new Date(d + "T00:00:00")),
  pName = (p) =>
    ({ high: "Tinggi", medium: "Sedang", low: "Rendah" })[p] || "Sedang";
function toast(m, type = "") {
  const x = document.createElement("div");
  x.className = "toast " + type;
  x.textContent = m;
  $("#toasts").append(x);
  setTimeout(() => x.remove(), 2600);
}
function counts() {
  return {
    todo: tasks.filter((x) => (x.status || "todo") === "todo").length,
    doing: tasks.filter((x) => x.status === "in_progress").length,
    done: tasks.filter((x) => x.status === "completed").length,
    late: tasks.filter((x) => x.status !== "completed" && days(x.deadline) < 0)
      .length,
  };
}
function memberMap() {
  const m = {};
  tasks.forEach((x) => {
    m[x.member] ??= { total: 0, doing: 0, done: 0 };
    m[x.member].total++;
    m[x.member].doing += x.status === "in_progress";
    m[x.member].done += x.status === "completed";
  });
  return m;
}
function filtered() {
  return tasks.filter(
    (x) =>
      `${x.title || x.task} ${x.member}`
        .toLowerCase()
        .includes(filters.search.toLowerCase()) &&
      (filters.member === "all" || x.member === filters.member) &&
      (filters.category === "all" || x.category === filters.category) &&
      (filters.priority === "all" || x.priority === filters.priority),
  );
}
function card(x) {
  const late = days(x.deadline) < 0 && x.status !== "completed";
  return `<article class="task-card" draggable="true" data-id="${x.id}"><div class="card-top"><h3>${esc(x.title || x.task)}</h3><button class="card-menu edit" data-id="${x.id}" type="button">•••</button></div>${x.description ? `<p class="description">${esc(x.description)}</p>` : ""}<div class="tags"><span class="tag ${x.priority}">${pName(x.priority)}</span><span class="tag category">${esc(x.category || "Lainnya")}</span></div><div class="card-meta"><span class="assignee"><i class="avatar">${initials(x.member)}</i>${esc(x.member)}</span><span class="due ${late ? "late" : ""}">${late ? "Terlambat · " : ""}${fmt(x.deadline)}</span></div><div class="card-actions"><button class="edit" data-id="${x.id}" type="button">Edit</button><button class="delete" data-id="${x.id}" type="button">Hapus</button></div></article>`;
}
function fillFilters() {
  const oldM = $("#memberFilter").value,
    oldC = $("#categoryFilter").value,
    members = [...new Set(tasks.map((x) => x.member).filter(Boolean))].sort(),
    cats = [...new Set(tasks.map((x) => x.category).filter(Boolean))].sort();
  $("#memberFilter").innerHTML =
    '<option value="all">Semua anggota</option>' +
    members.map((x) => `<option>${esc(x)}</option>`).join("");
  $("#categoryFilter").innerHTML =
    '<option value="all">Semua kategori</option>' +
    cats.map((x) => `<option>${esc(x)}</option>`).join("");
  $("#memberFilter").value = members.includes(oldM) ? oldM : "all";
  $("#categoryFilter").value = cats.includes(oldC) ? oldC : "all";
}
function render() {
  const c = counts(),
    pct = tasks.length ? Math.round((c.done / tasks.length) * 100) : 0;
  $("#sumAll").textContent = tasks.length;
  $("#sumTodo").textContent = c.todo;
  $("#sumDoing").textContent = c.doing;
  $("#sumDone").textContent = c.done;
  $("#sumLate").textContent = c.late;
  $("#countTodo").textContent = c.todo;
  $("#countDoing").textContent = c.doing;
  $("#countDone").textContent = c.done;
  $("#progressLabel").textContent = pct + "%";
  $("#progressBar").style.width = pct + "%";
  const list = filtered();
  ["todo", "in_progress", "completed"].forEach((s) => {
    const here = list.filter((x) => (x.status || "todo") === s),
      el = $(`[data-list="${s}"]`);
    el.innerHTML = here.length
      ? here.map(card).join("")
      : '<div class="empty">Belum ada tugas di kolom ini.</div>';
  });
  renderMembers();
  bindDrag();
}
function renderMembers() {
  const m = memberMap(),
    names = Object.keys(m);
  $("#memberStack").innerHTML = names
    .slice(0, 5)
    .map((n) => `<span title="${esc(n)}">${initials(n)}</span>`)
    .join("");
  $("#membersGrid").innerHTML = names.length
    ? names
        .map(
          (n) =>
            `<article class="member-card"><div class="large-avatar">${initials(n)}</div><h3>${esc(n)}</h3><p>Anggota kelompok Cloud Computing</p><div class="member-stats"><div><strong>${m[n].total}</strong><small>Total tugas</small></div><div><strong>${m[n].doing}</strong><small>Dikerjakan</small></div><div><strong>${m[n].done}</strong><small>Selesai</small></div></div></article>`,
        )
        .join("")
    : '<div class="empty">Anggota akan muncul setelah tugas ditambahkan.</div>';
}
async function load() {
  try {
    const r = await fetch("/api/tasks", { cache: "no-store" });
    if (!r.ok) throw Error("Backend tidak dapat dihubungi");
    const j = await r.json();
    tasks = j.data || [];
    $("#apiDot").className = "online";
    $("#apiText").textContent = "API aktif";
    fillFilters();
    render();
  } catch (e) {
    $("#apiDot").className = "offline";
    $("#apiText").textContent = "API tidak aktif";
    toast(e.message, "error");
  }
}
function openForm(item = null, status = "todo") {
  editing = item?.id || null;
  formStatus = item?.status || status;
  $("#formEyebrow").textContent = item ? "EDIT TUGAS" : "TUGAS BARU";
  $("#modalTitle").textContent = item ? "Edit tugas" : "Tambah tugas";
  $("#fTitle").value = item?.title || item?.task || "";
  $("#fDesc").value = item?.description || "";
  $("#fMember").value = item?.member || "";
  $("#fDeadline").value =
    item?.deadline || new Date(Date.now() + 864e5).toISOString().slice(0, 10);
  $("#fCategory").value = item?.category || "Backend API";
  $("#fPriority").value = item?.priority || "medium";
  $("#modal").hidden = false;
  setTimeout(() => $("#fTitle").focus(), 30);
}
function close() {
  editing = null;
  $("#modal").hidden = true;
  $("#form").reset();
}
$("#newTask").onclick = () => openForm();
$$("[data-add]").forEach(
  (b) => (b.onclick = () => openForm(null, b.dataset.add)),
);
$("#close").onclick = close;
$("#cancel").onclick = close;
$("#modal").onclick = (e) => {
  if (e.target === $("#modal")) close();
};
$("#form").onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    title: $("#fTitle").value.trim(),
    description: $("#fDesc").value.trim(),
    member: $("#fMember").value.trim(),
    deadline: $("#fDeadline").value,
    category: $("#fCategory").value,
    priority: $("#fPriority").value,
    status: formStatus,
  };
  try {
    const r = await fetch("/api/tasks" + (editing ? "?id=" + editing : ""), {
        method: editing ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
      j = await r.json();
    if (!r.ok) throw Error(j.message);
    close();
    toast(editing ? "Tugas diperbarui" : "Tugas ditambahkan");
    await load();
  } catch (x) {
    toast(x.message, "error");
  }
};
$("#boardView").onclick = (e) => {
  const id = e.target.dataset.id;
  if (!id) return;
  if (e.target.classList.contains("edit"))
    return openForm(tasks.find((x) => x.id === id));
  if (e.target.classList.contains("delete")) {
    if (confirm("Hapus tugas ini secara permanen?"))
      request("/api/tasks?id=" + id, "DELETE");
  }
};
async function request(url, method, body) {
  try {
    const r = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: body ? JSON.stringify(body) : undefined,
      }),
      j = await r.json();
    if (!r.ok) throw Error(j.message);
    toast(j.message);
    await load();
  } catch (e) {
    toast(e.message, "error");
  }
}
function bindDrag() {
  let dragged = null;
  $$(".task-card").forEach((c) => {
    c.ondragstart = () => {
      dragged = c.dataset.id;
      c.classList.add("dragging");
    };
    c.ondragend = () => {
      c.classList.remove("dragging");
      $$(".cards").forEach((x) => x.classList.remove("drag-over"));
    };
  });
  $$(".cards").forEach((l) => {
    l.ondragover = (e) => {
      e.preventDefault();
      l.classList.add("drag-over");
    };
    l.ondragleave = () => l.classList.remove("drag-over");
    l.ondrop = (e) => {
      e.preventDefault();
      l.classList.remove("drag-over");
      const status = l.dataset.list,
        item = tasks.find((x) => x.id === dragged);
      if (item && item.status !== status)
        request("/api/tasks/status?id=" + dragged, "PATCH", { status });
    };
  });
}
$$(".nav-item").forEach(
  (b) =>
    (b.onclick = () => {
      $$(".nav-item").forEach((x) => x.classList.remove("active"));
      b.classList.add("active");
      $$(".view").forEach((x) => x.classList.remove("active"));
      $("#" + b.dataset.view + "View").classList.add("active");
      $("#sidebar").classList.remove("open");
    }),
);
$("#mobileMenu").onclick = () => $("#sidebar").classList.toggle("open");
$("#search").oninput = (e) => {
  filters.search = e.target.value;
  render();
};
$("#memberFilter").onchange = (e) => {
  filters.member = e.target.value;
  render();
};
$("#categoryFilter").onchange = (e) => {
  filters.category = e.target.value;
  render();
};
$("#priorityFilter").onchange = (e) => {
  filters.priority = e.target.value;
  render();
};
$("#clearFilters").onclick = () => {
  filters = { search: "", member: "all", category: "all", priority: "all" };
  $("#search").value = "";
  $("#memberFilter").value = "all";
  $("#categoryFilter").value = "all";
  $("#priorityFilter").value = "all";
  render();
};
document.onkeydown = (e) => {
  if (e.key === "Escape") close();
};
load();
