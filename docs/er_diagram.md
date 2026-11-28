# ER-диаграмма хранилища данных

Предметная область — сквозной проект варианта 7 (логические векторы по вещественной матрице n × m).
Диаграмма отображается на GitHub автоматически (Mermaid); картинка — `docs/er_diagram.png`.

```mermaid
erDiagram
    MATRIX ||--o{ MATRIX_CELL : "содержит"
    MATRIX ||--o{ ANALYSIS : "обрабатывается"
    ANALYSIS ||--o{ VECTOR_RESULT : "даёт"
    MATRIX ||--o{ MATRIX_TAG : "помечается"
    TAG ||--o{ MATRIX_TAG : "назначается"
    MATRIX {
        int id PK
        string name UK
        int n_rows
        int n_cols
        datetime created_at
        string note
    }
    MATRIX_CELL {
        int id PK
        int matrix_id FK
        int row_idx
        int col_idx
        float value
    }
    TAG {
        int id PK
        string name UK
    }
    MATRIX_TAG {
        int matrix_id PK
        int tag_id PK
    }
    ANALYSIS {
        int id PK
        int matrix_id FK
        float eps
        datetime created_at
    }
    VECTOR_RESULT {
        int id PK
        int analysis_id FK
        string kind
        int position
        bool value
    }
    SETTING {
        string key PK
        string value
    }
```

## Сущности и связи

| Сущность | Назначение | Связи |
|---|---|---|
| `matrix` | Сохранённая матрица: имя, размеры, примечание | 1:N с `matrix_cell` и `analysis`; M:N с `tag` |
| `matrix_cell` | Один элемент матрицы (строка, столбец, значение) | N:1 к `matrix` |
| `tag` | Тег для группировки и фильтрации матриц | M:N с `matrix` через `matrix_tag` |
| `matrix_tag` | Связующая таблица M:N | N:1 к `matrix` и `tag` |
| `analysis` | Запуск обработки матрицы (параметр `eps`, время) | N:1 к `matrix`; 1:N с `vector_result` |
| `vector_result` | Элемент одного из трёх логических векторов | N:1 к `analysis` |
| `setting` | Настройки пользователя (адаптация интерфейса) | не связана |
