"""Загрузка и агрегация JSON-контента для рендеринга по локали."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONTENT_DIR = Path(__file__).resolve().parent


def load_json(file_path: Path | str) -> Any:
    """Загружает JSON-файл и возвращает его содержимое."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def normalize_key(file_name: str) -> str:
    """Преобразует имя файла в ключ контекста (дефис → подчёркивание)."""
    return file_name.replace('-', '_')


def load_locale_content(locale: str = 'ru') -> dict[str, Any]:
    """Загружает все JSON-файлы локали и возвращает словарь ключ→данные."""
    locale_dir = CONTENT_DIR / locale
    if not locale_dir.exists():
        raise FileNotFoundError(f'Директория локали не найдена: {locale_dir}')
    content: dict[str, Any] = {}
    for file_path in locale_dir.glob('*.json'):
        key = normalize_key(file_path.stem)
        content[key] = load_json(file_path)
    return content


def build_context(locale: str = 'ru') -> dict[str, Any]:
    """Возвращает полный контекст рендеринга для указанной локали."""
    return load_locale_content(locale)
