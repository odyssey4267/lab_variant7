"""Тесты REST API (FastAPI TestClient): коды ответов, форматы, ошибки, настройки."""

import pytest

SAMPLE = [[3, 2, 0], [0, 5, 0]]
URL = "/api/v1/matrices"


def add(client, name="m1", data=SAMPLE, tags=()):
    return client.post(URL, json={"name": name, "data": data, "tags": list(tags)})


def test_health(client):
    assert client.get("/api/v1/health").json() == {"status": "ok"}


def test_index_page_and_swagger(client):
    page = client.get("/")
    assert page.status_code == 200 and "Swagger UI" in page.text
    assert client.get("/docs").status_code == 200
    paths = client.get("/openapi.json").json()["paths"]
    assert URL in paths and URL + "/{matrix_id}" in paths


# ------------------------------------------------------------ создание
def test_create_returns_201_and_body(client):
    resp = add(client, "m1", SAMPLE, ["Demo", "a"])
    body = resp.json()
    assert resp.status_code == 201
    assert body["name"] == "m1" and (body["rows"], body["cols"]) == (2, 3)
    assert body["tags"] == ["a", "demo"] and body["data"] == [[3, 2, 0], [0, 5, 0]]


def test_create_duplicate_gives_409(client):
    add(client)
    assert add(client).status_code == 409


@pytest.mark.parametrize("payload", [
    {"data": SAMPLE},                                  # нет имени
    {"name": "", "data": SAMPLE},                      # пустое имя
    {"name": "x" * 101, "data": SAMPLE},               # слишком длинное имя
    {"name": "m", "data": "text"},                     # данные не массив
    {"name": "m", "data": [[1, "a"]]},                 # нечисловой элемент
    {"name": "m", "data": []},                         # пустая матрица
    {"name": "m", "data": [[]]},                       # нет столбцов
    {"name": "m", "data": [[1], [1, 2]]},              # неровные строки
])
def test_create_invalid_payload_gives_422(client, payload):
    assert client.post(URL, json=payload).status_code == 422


# ------------------------------------------------------------ чтение, изменение, удаление
def test_get_matrix(client):
    created = add(client).json()
    resp = client.get(f"{URL}/{created['id']}")
    assert resp.status_code == 200 and resp.json()["data"] == [[3, 2, 0], [0, 5, 0]]


def test_get_missing_gives_404(client):
    assert client.get(URL + "/999").status_code == 404


def test_get_with_non_integer_id_gives_422(client):
    assert client.get(URL + "/abc").status_code == 422


def test_put_changes_fields(client):
    mid = add(client, "m1", SAMPLE, ["x"]).json()["id"]
    resp = client.put(f"{URL}/{mid}", json={"name": "m2", "data": [[1, 2]], "tags": ["y"]})
    body = resp.json()
    assert resp.status_code == 200
    assert (body["name"], body["rows"], body["cols"], body["tags"]) == ("m2", 1, 2, ["y"])


def test_put_partial_keeps_other_fields(client):
    mid = add(client, "m1", SAMPLE, ["x"]).json()["id"]
    body = client.put(f"{URL}/{mid}", json={"name": "renamed"}).json()
    assert body["name"] == "renamed" and body["tags"] == ["x"] and body["rows"] == 2


def test_put_errors(client):
    add(client, "taken")
    mid = add(client, "other").json()["id"]
    assert client.put(f"{URL}/999", json={"name": "z"}).status_code == 404
    assert client.put(f"{URL}/{mid}", json={"name": "taken"}).status_code == 409
    assert client.put(f"{URL}/{mid}", json={"data": [[1], [1, 2]]}).status_code == 422


def test_delete_matrix(client):
    mid = add(client).json()["id"]
    assert client.delete(f"{URL}/{mid}").status_code == 204
    assert client.get(f"{URL}/{mid}").status_code == 404
    assert client.delete(f"{URL}/{mid}").status_code == 404


# ------------------------------------------------------------ список
@pytest.fixture
def filled(client):
    for name, tags in (("delta", ["x"]), ("alpha", ["x", "y"]), ("charlie", []),
                       ("bravo", ["y"]), ("echo", ["x"])):
        add(client, name, SAMPLE, tags)
    return client


def listed(client, **params):
    resp = client.get(URL, params=params)
    assert resp.status_code == 200
    return [item["name"] for item in resp.json()["items"]], resp.json()


def test_list_has_no_matrix_data(filled):
    _, body = listed(filled)
    assert body["total"] == 5 and body["items"][0]["data"] is None


def test_list_filters(filled):
    assert set(listed(filled, tag="x")[0]) == {"delta", "alpha", "echo"}
    assert listed(filled, q="LPH")[0] == ["alpha"]
    assert listed(filled, tag="nope")[1]["total"] == 0


def test_list_sort_and_pages(filled):
    assert listed(filled, sort_by="name", order="asc")[0][:2] == ["alpha", "bravo"]
    assert listed(filled, sort_by="name", order="desc")[0][0] == "echo"
    names, body = listed(filled, sort_by="name", limit=2, offset=4)
    assert names == ["echo"] and body["total"] == 5 and body["limit"] == 2


@pytest.mark.parametrize("params", [
    {"sort_by": "password"}, {"order": "up"}, {"limit": 0}, {"limit": 101}, {"offset": -1},
])
def test_list_invalid_params_give_422(filled, params):
    assert filled.get(URL, params=params).status_code == 422


# ------------------------------------------------------------ анализ
def test_run_analysis(client):
    mid = add(client).json()["id"]
    resp = client.post(f"{URL}/{mid}/analyses", json={})
    body = resp.json()
    assert resp.status_code == 201 and body["matrix_id"] == mid
    assert body["zero_columns"] == [False, False, True]
    assert body["descending_rows"] == [True, False]
    assert body["symmetric_rows"] == [False, True]


def test_run_analysis_without_body_and_with_eps(client):
    mid = add(client, "tiny", [[0.001, 1.0]]).json()["id"]
    assert client.post(f"{URL}/{mid}/analyses").status_code == 201
    loose = client.post(f"{URL}/{mid}/analyses", json={"eps": 0.01}).json()
    assert loose["zero_columns"] == [True, False] and loose["eps"] == 0.01


def test_analysis_errors(client):
    mid = add(client).json()["id"]
    assert client.post(f"{URL}/999/analyses", json={}).status_code == 404
    assert client.post(f"{URL}/{mid}/analyses", json={"eps": -1}).status_code == 422
    assert client.get("/api/v1/analyses/999").status_code == 404
    assert client.get(f"{URL}/999/analyses").status_code == 404


def test_analysis_history_and_lookup(client):
    mid = add(client).json()["id"]
    first = client.post(f"{URL}/{mid}/analyses", json={}).json()
    client.post(f"{URL}/{mid}/analyses", json={})
    history = client.get(f"{URL}/{mid}/analyses").json()
    assert len(history) == 2
    assert client.get(f"/api/v1/analyses/{first['id']}").json()["id"] == first["id"]


# ------------------------------------------------------------ настройки
def test_default_settings(client):
    assert client.get("/api/v1/settings").json() == {
        "eps": 1e-9, "page_size": 10, "sort_by": "id", "order": "asc"}


def test_settings_change_default_listing(filled):
    resp = filled.put("/api/v1/settings", json={"page_size": 2, "sort_by": "name", "order": "desc"})
    assert resp.status_code == 200 and resp.json()["page_size"] == 2
    names, body = listed(filled)
    assert names == ["echo", "delta"] and body["limit"] == 2


def test_settings_eps_is_used_by_analysis(client):
    mid = add(client, "tiny", [[0.001, 1.0]]).json()["id"]
    client.put("/api/v1/settings", json={"eps": 0.01})
    body = client.post(f"{URL}/{mid}/analyses", json={}).json()
    assert body["zero_columns"][0] is True


@pytest.mark.parametrize("payload", [
    {"page_size": 0}, {"page_size": 101}, {"eps": -1}, {"order": "up"}, {"sort_by": "zzz"},
])
def test_invalid_settings_give_422(client, payload):
    assert client.put("/api/v1/settings", json=payload).status_code == 422


def test_note_roundtrip(client):
    body = client.post(URL, json={"name": "n", "data": SAMPLE, "note": "заметка"}).json()
    assert body["note"] == "заметка"
    changed = client.put(f"{URL}/{body['id']}", json={"note": "другая"}).json()
    assert changed["note"] == "другая"


def test_note_too_long_gives_422(client):
    payload = {"name": "n", "data": SAMPLE, "note": "x" * 201}
    assert client.post(URL, json=payload).status_code == 422
