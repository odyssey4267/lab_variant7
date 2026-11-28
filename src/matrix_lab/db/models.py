"""ORM-модели хранилища (SQLAlchemy 2.0). Схема приведена к 3НФ."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, Float, ForeignKey, Integer, String, Table,
    UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Базовый класс всех моделей."""


# Связь «многие ко многим»: матрица <-> тег.
matrix_tag = Table(
    "matrix_tag",
    Base.metadata,
    Column("matrix_id", ForeignKey("matrix.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tag.id", ondelete="CASCADE"), primary_key=True),
)


class MatrixRecord(Base):
    """Сохранённая матрица (заголовок: имя и размеры)."""

    __tablename__ = "matrix"
    __table_args__ = (
        CheckConstraint("n_rows >= 1", name="ck_matrix_rows"),
        CheckConstraint("n_cols >= 1", name="ck_matrix_cols"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    n_rows: Mapped[int] = mapped_column(Integer, nullable=False)
    n_cols: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False)
    note: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    cells: Mapped[List["MatrixCell"]] = relationship(
        back_populates="matrix", cascade="all, delete-orphan",
        order_by="MatrixCell.row_idx, MatrixCell.col_idx")
    analyses: Mapped[List["Analysis"]] = relationship(
        back_populates="matrix", cascade="all, delete-orphan", order_by="Analysis.id")
    tags: Mapped[List["Tag"]] = relationship(secondary=matrix_tag, back_populates="matrices")


class MatrixCell(Base):
    """Один элемент матрицы: позиция (строка, столбец) и значение."""

    __tablename__ = "matrix_cell"
    __table_args__ = (UniqueConstraint("matrix_id", "row_idx", "col_idx", name="uq_cell_pos"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    matrix_id: Mapped[int] = mapped_column(
        ForeignKey("matrix.id", ondelete="CASCADE"), nullable=False, index=True)
    row_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    col_idx: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    matrix: Mapped["MatrixRecord"] = relationship(back_populates="cells")


class Tag(Base):
    """Тег для группировки матриц."""

    __tablename__ = "tag"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    matrices: Mapped[List["MatrixRecord"]] = relationship(
        secondary=matrix_tag, back_populates="tags")


class Analysis(Base):
    """Запуск обработки матрицы: параметр eps и время запуска."""

    __tablename__ = "analysis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    matrix_id: Mapped[int] = mapped_column(
        ForeignKey("matrix.id", ondelete="CASCADE"), nullable=False, index=True)
    eps: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp(), nullable=False)

    matrix: Mapped["MatrixRecord"] = relationship(back_populates="analyses")
    results: Mapped[List["VectorResult"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan",
        order_by="VectorResult.kind, VectorResult.position")


class VectorResult(Base):
    """Элемент одного из трёх логических векторов результата."""

    __tablename__ = "vector_result"
    __table_args__ = (
        UniqueConstraint("analysis_id", "kind", "position", name="uq_result_pos"),
        CheckConstraint(
            "kind IN ('zero_columns', 'descending_rows', 'symmetric_rows')", name="ck_result_kind"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(
        ForeignKey("analysis.id", ondelete="CASCADE"), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    value: Mapped[bool] = mapped_column(Boolean, nullable=False)

    analysis: Mapped["Analysis"] = relationship(back_populates="results")


class Setting(Base):
    """Пользовательская настройка (адаптация интерфейса): ключ и значение."""

    __tablename__ = "setting"

    key: Mapped[str] = mapped_column(String(50), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), nullable=False)


__all__ = [
    "Analysis", "Base", "MatrixCell", "MatrixRecord", "Setting", "Tag",
    "VectorResult", "matrix_tag",
]
