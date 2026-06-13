"""Рендеринг Jinja2-шаблонов и постобработка HTML (minify / prettier)."""
from __future__ import annotations

import os
import shutil
import subprocess
from typing import Any

from htmlmin import minify
from jinja2 import Environment, FileSystemLoader

from content.content_loader import build_context


def _ru_plural(n: int, one: str, few: str, many: str) -> str:
    """Возвращает правильную форму русского существительного по числу."""
    mod10, mod100 = n % 10, n % 100
    if mod100 in range(11, 20):
        return many
    if mod10 == 1:
        return one
    if mod10 in range(2, 5):
        return few
    return many


def render_template(
    template_name: str,
    context: dict[str, Any] | None = None,
    template_dir: str = './html_generator/templates',
) -> str:
    """Рендерит Jinja2-шаблон с переданным контекстом и возвращает HTML-строку."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        lstrip_blocks=True,
        trim_blocks=True
    )
    env.filters['ru_tasks'] = lambda n: f"{n} {_ru_plural(n, 'задача', 'задачи', 'задач')}"
    template = env.get_template(template_name)
    if context is None:
        context = {}
    return template.render(context)


def generate_index_page(
    output_dir: str,
    template_dir: str,
    index_file: str,
    mode: str,
    locale: str = 'ru',
    static_version: str = '',
) -> None:
    """Рендерит и сохраняет index.html для указанной локали и режима."""
    os.makedirs(output_dir, exist_ok=True)

    context = build_context(locale)

    context.update({
        'locale': locale,
        'current_lang': locale,
        'ru_url': '/ru/',
        'en_url': '/en/',
        'static_version': static_version,
    })

    rendered_html = render_template(
        'base.html',
        context=context,
        template_dir=template_dir
    )

    file_path = os.path.join(output_dir, index_file)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(rendered_html)

    if mode == 'prettier':
        format_with_prettier(file_path)
    elif mode == 'minify':
        minify_html(file_path, rendered_html)
    else:
        raise ValueError(
            f'Неизвестный режим: {mode}. '
            'Используйте "prettier" или "minify".'
        )


def format_with_prettier(file_path: str) -> None:
    """Форматирует HTML-файл через Prettier (требует npx в PATH)."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'Файл {file_path} не найден.')
    npx_path = shutil.which('npx')
    if not npx_path:
        raise FileNotFoundError(
            "Команда 'npx' не найдена. Установи Node.js и npm, затем выполни 'npm install' в папке source."
        )
    prettier_command = [npx_path, 'prettier', '--write', file_path]
    try:
        subprocess.run(
            prettier_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print('Файл успешно отформатирован с помощью Prettier.')
    except subprocess.CalledProcessError as e:
        print(f'Ошибка при форматировании файла: {e.stderr}')


def minify_html(file_path: str, rendered_html: str) -> None:
    """Минифицирует HTML и перезаписывает файл."""
    minified_html = minify(rendered_html)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(minified_html)
    print('HTML успешно минифицирован.')
