-- Тестовые данные: две матрицы, теги и один сохранённый анализ.

INSERT INTO matrix (name, n_rows, n_cols) VALUES ('example1', 2, 3);
INSERT INTO matrix (name, n_rows, n_cols) VALUES ('palindromes', 2, 3);

INSERT INTO matrix_cell (matrix_id, row_idx, col_idx, value) VALUES
    (1, 0, 0, 3.0), (1, 0, 1, 2.0), (1, 0, 2, 0.0),
    (1, 1, 0, 0.0), (1, 1, 1, 5.0), (1, 1, 2, 0.0),
    (2, 0, 0, 1.0), (2, 0, 1, 2.0), (2, 0, 2, 1.0),
    (2, 1, 0, 4.0), (2, 1, 1, 4.0), (2, 1, 2, 4.0);

INSERT INTO tag (name) VALUES ('demo'), ('symmetric');
INSERT INTO matrix_tag (matrix_id, tag_id) VALUES (1, 1), (2, 1), (2, 2);

INSERT INTO analysis (matrix_id, eps) VALUES (1, 1e-9);
INSERT INTO vector_result (analysis_id, kind, position, value) VALUES
    (1, 'zero_columns', 0, 0), (1, 'zero_columns', 1, 0), (1, 'zero_columns', 2, 1),
    (1, 'descending_rows', 0, 1), (1, 'descending_rows', 1, 0),
    (1, 'symmetric_rows', 0, 0), (1, 'symmetric_rows', 1, 1);

INSERT INTO setting (key, value) VALUES ('eps', '1e-9'), ('page_size', '10');
