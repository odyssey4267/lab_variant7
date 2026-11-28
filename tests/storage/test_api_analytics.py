"""Тесты маршрутов интеллектуального анализа (уровень 3)."""

import pytest

URL = "/api/v1/matrices"


@pytest.fixture
def mid(client):
    body = {"name": "m", "data": [[1, 2, 3], [4, 4, 4], [0, -1, -2]]}
    return client.post(URL, json=body).json()["id"]


def test_statistics(client, mid):
    body = client.get(f"{URL}/{mid}/statistics").json()
    assert body["max"] == 4 and body["min"] == -2
    assert body["row_sums"] == [6, 12, -3]
    assert body["mean"] == pytest.approx(15 / 9)


def test_forecast(client, mid):
    body = client.get(f"{URL}/{mid}/forecast", params={"row": 0, "steps": 2}).json()
    assert body["forecast"] == pytest.approx([4.0, 5.0])
    assert body["slope"] == pytest.approx(1.0)


def test_forecast_defaults(client, mid):
    assert len(client.get(f"{URL}/{mid}/forecast").json()["forecast"]) == 3


@pytest.mark.parametrize("params", [{"row": 7}, {"steps": 0}, {"steps": 21}, {"row": -1}])
def test_forecast_invalid_params(client, mid, params):
    assert client.get(f"{URL}/{mid}/forecast", params=params).status_code == 422


def test_forecast_needs_two_elements(client):
    one = client.post(URL, json={"name": "one", "data": [[5]]}).json()["id"]
    assert client.get(f"{URL}/{one}/forecast").status_code == 422


def test_analytics_of_missing_matrix(client):
    assert client.get(f"{URL}/99/statistics").status_code == 404
    assert client.get(f"{URL}/99/forecast").status_code == 404


def test_summary_empty_and_filled(client, mid):
    assert client.get("/api/v1/analytics/summary").json() == {"analyses": 0, "vectors": {}}
    client.post(f"{URL}/{mid}/analyses", json={})
    body = client.get("/api/v1/analytics/summary").json()
    assert body["analyses"] == 1
    assert body["vectors"]["zero_columns"]["total"] == 3
    assert set(body["vectors"]) == {"zero_columns", "descending_rows", "symmetric_rows"}
