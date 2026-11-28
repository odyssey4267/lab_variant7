"""Веб-страница интерфейса (одна страница, без внешних библиотек)."""

INDEX_HTML = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Матрицы и логические векторы</title>
<style>
  body { font-family: sans-serif; margin: 24px auto; max-width: 900px; padding: 0 12px; }
  fieldset { margin-bottom: 16px; }
  label { margin-right: 12px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #999; padding: 4px 8px; text-align: left; }
  #msg { color: #a00; min-height: 1.5em; }
  pre { background: #f4f4f4; padding: 8px; }
</style>
</head>
<body>
<h1>Матрицы и логические векторы</h1>
<p>Документация API: <a href="/docs">Swagger UI</a></p>
<div id="msg"></div>

<fieldset><legend>Новая матрица</legend>
  <label>Имя <input id="name"></label>
  <label>Теги (через запятую) <input id="tags"></label><br>
  <p>Строки матрицы — с новой строки, числа — через пробел:</p>
  <textarea id="data" rows="4" cols="40">3 2 0
0 5 0</textarea><br>
  <button id="add">Сохранить</button>
</fieldset>

<fieldset><legend>Фильтры и сортировка</legend>
  <label>Тег <input id="f-tag" size="10"></label>
  <label>Имя содержит <input id="f-q" size="10"></label>
  <label>Сортировка
    <select id="f-sort">
      <option>id</option><option>name</option><option>created_at</option>
      <option>n_rows</option><option>n_cols</option>
    </select>
  </label>
  <label><select id="f-order"><option>asc</option><option>desc</option></select></label>
  <label>На странице <input id="f-size" type="number" min="1" max="100" size="3"></label>
  <button id="apply">Применить</button>
  <button id="save-prefs">Запомнить настройки</button>
</fieldset>

<table>
  <thead><tr><th>id</th><th>Имя</th><th>n × m</th><th>Теги</th><th>Действия</th></tr></thead>
  <tbody id="rows"></tbody>
</table>
<p id="total"></p>
<pre id="result"></pre>

<script>
const API = "/api/v1";
const $ = (id) => document.getElementById(id);

function show(text) { $("msg").textContent = text || ""; }

async function call(method, url, body) {
  const resp = await fetch(API + url, {
    method,
    headers: {"Content-Type": "application/json"},
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (resp.status === 204) { return null; }
  const payload = await resp.json();
  if (!resp.ok) { throw new Error(JSON.stringify(payload.detail || payload)); }
  return payload;
}

async function loadPrefs() {
  const s = await call("GET", "/settings");
  $("f-sort").value = s.sort_by;
  $("f-order").value = s.order;
  $("f-size").value = s.page_size;
}

async function savePrefs() {
  await call("PUT", "/settings", {
    sort_by: $("f-sort").value, order: $("f-order").value, page_size: Number($("f-size").value),
  });
  show("Настройки сохранены.");
}

function cell(text) { const td = document.createElement("td"); td.textContent = text; return td; }

function button(label, handler) {
  const b = document.createElement("button");
  b.textContent = label;
  b.addEventListener("click", () => handler().catch((e) => show(e.message)));
  return b;
}

async function analyze(id) {
  const res = await call("POST", "/matrices/" + id + "/analyses", {});
  $("result").textContent = "Анализ матрицы " + id + ":\\n" + JSON.stringify(res, null, 2);
}

async function remove(id) {
  await call("DELETE", "/matrices/" + id);
  await refresh();
}

async function refresh() {
  const p = new URLSearchParams({
    sort_by: $("f-sort").value, order: $("f-order").value, limit: $("f-size").value || 10,
  });
  if ($("f-tag").value) { p.set("tag", $("f-tag").value); }
  if ($("f-q").value) { p.set("q", $("f-q").value); }
  const page = await call("GET", "/matrices?" + p.toString());
  const body = $("rows");
  body.textContent = "";
  for (const m of page.items) {
    const tr = document.createElement("tr");
    tr.append(cell(m.id), cell(m.name), cell(m.rows + " × " + m.cols), cell(m.tags.join(", ")));
    const actions = document.createElement("td");
    actions.append(button("Обработать", () => analyze(m.id)));
    actions.append(button("Удалить", () => remove(m.id)));
    tr.append(actions);
    body.append(tr);
  }
  $("total").textContent = "Всего по фильтру: " + page.total;
}

async function add() {
  const data = $("data").value.trim().split("\\n").map(
    (line) => line.trim().split(/\\s+/).map(Number));
  const tags = $("tags").value.split(",").map((t) => t.trim()).filter(Boolean);
  await call("POST", "/matrices", {name: $("name").value, data, tags});
  show("Матрица сохранена.");
  await refresh();
}

$("add").addEventListener("click", () => add().catch((e) => show(e.message)));
$("apply").addEventListener("click", () => refresh().catch((e) => show(e.message)));
$("save-prefs").addEventListener("click", () => savePrefs().catch((e) => show(e.message)));
loadPrefs().then(refresh).catch((e) => show(e.message));
</script>
</body>
</html>
"""
