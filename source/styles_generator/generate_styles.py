"""Поиск, объединение и минификация CSS-файлов."""
from __future__ import annotations

import os

from csscompressor import compress


def find_css_files(directory: str) -> list[str]:
    """Рекурсивно находит все CSS-файлы в указанной директории."""
    css_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.css'):
                css_files.append(os.path.join(root, file))
    return css_files


def combine_and_minify_css(input_files: list[str], output_file: str) -> None:
    """Объединяет CSS-файлы в один и сохраняет минифицированный результат."""
    combined_content = ""
    for file_path in input_files:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f'Файл {file_path} не найден.')
        with open(file_path, 'r', encoding='utf-8') as file:
            combined_content += file.read() + "\n"
    minified_css = compress(combined_content)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(minified_css)
    print('CSS успешно объединен и минифицирован.')
