-- Схема хранилища данных «Логические векторы по матрице» (SQLite, 3НФ).
-- Выполняется командой: python tools/db_check.py

PRAGMA foreign_keys = ON;

CREATE TABLE matrix (
    id         INTEGER      PRIMARY KEY AUTOINCREMENT,
    name       VARCHAR(100) NOT NULL UNIQUE,
    n_rows     INTEGER      NOT NULL CHECK (n_rows >= 1),
    n_cols     INTEGER      NOT NULL CHECK (n_cols >= 1),
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    note       VARCHAR(200)              -- добавлено миграцией 0002
);

CREATE TABLE matrix_cell (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    matrix_id INTEGER NOT NULL REFERENCES matrix (id) ON DELETE CASCADE,
    row_idx   INTEGER NOT NULL CHECK (row_idx >= 0),
    col_idx   INTEGER NOT NULL CHECK (col_idx >= 0),
    value     FLOAT   NOT NULL,
    UNIQUE (matrix_id, row_idx, col_idx)
);

CREATE TABLE tag (
    id   INTEGER     PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE matrix_tag (
    matrix_id INTEGER NOT NULL REFERENCES matrix (id) ON DELETE CASCADE,
    tag_id    INTEGER NOT NULL REFERENCES tag (id) ON DELETE CASCADE,
    PRIMARY KEY (matrix_id, tag_id)
);

CREATE TABLE analysis (
    id         INTEGER  PRIMARY KEY AUTOINCREMENT,
    matrix_id  INTEGER  NOT NULL REFERENCES matrix (id) ON DELETE CASCADE,
    eps        FLOAT    NOT NULL CHECK (eps >= 0),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE vector_result (
    id          INTEGER     PRIMARY KEY AUTOINCREMENT,
    analysis_id INTEGER     NOT NULL REFERENCES analysis (id) ON DELETE CASCADE,
    kind        VARCHAR(20) NOT NULL
        CHECK (kind IN ('zero_columns', 'descending_rows', 'symmetric_rows')),
    position    INTEGER     NOT NULL CHECK (position >= 0),
    value       BOOLEAN     NOT NULL,
    UNIQUE (analysis_id, kind, position)
);

CREATE TABLE setting (
    key   VARCHAR(50)  PRIMARY KEY,
    value VARCHAR(200) NOT NULL
);

CREATE INDEX ix_matrix_cell_matrix ON matrix_cell (matrix_id);
CREATE INDEX ix_analysis_matrix ON analysis (matrix_id);
CREATE INDEX ix_vector_result_analysis ON vector_result (analysis_id);
