"""Точка входа генератора статического сайта: HTML, CSS, JS и SVG-шилды."""
from __future__ import annotations

import argparse
import os
import time

from html_generator.generate_html import generate_index_page
from shields_generator.generate_shields import (
    generate_custom_svg, read_params_from_csv,
    generate_shield_template
)
from styles_generator.generate_styles import (
    find_css_files, combine_and_minify_css
)
from scripts_generator.generate_scripts import process_scripts


CONFIG = {
    'html': {
        'output_directory': '../static',
        'template_directory': './html_generator/templates',
        'index_file': 'index.html',
        'content_directory': './content',
        'languages': ['ru', 'en'],
        'default_language': 'ru',
    },
    'scripts': {
        'input_directory': './scripts_generator/scripts',
        'output_directory': '../static/scripts',
    },
    'css': {
        'directory': './styles_generator/styles/',
        'target_directory': '../static/styles/',
        'minified_file': 'main.css',
    },
    'shields': {
        'data_directory': './shields_generator/csv_data',
        'target_base_directory': '../static/images/shields',
        'template_path': './shields_generator/template.svg',
        'color': 'blue',
        'logo_color': '#21e7e7',
        'new_height': '30',
        'time_sleep': 0,
        'scale_factors': {
            'width_scale_factor': 0.9,
            'text_length_scale_factor': 0.85,
            'x_scale_factor': 0.87,
            'y_scale_factor': 0.9,
        },
    },
}


def clear_directories(directories: list[str]) -> None:
    """Удаляет и пересоздаёт указанные директории."""
    for directory in directories:
        try:
            if os.path.exists(directory):
                for root, dirs, files in os.walk(directory, topdown=False):
                    for file in files:
                        os.remove(os.path.join(root, file))
                    for dir in dirs:
                        os.rmdir(os.path.join(root, dir))
                os.rmdir(directory)
                print(f'Директория {directory} успешно удалена.')
            os.makedirs(directory, exist_ok=True)
            print(f'Директория {directory} успешно создана.')
        except Exception as e:
            print(f'Ошибка при работе с директорией {directory}: {e}')


def generate_shields() -> None:
    """Генерирует SVG-шилды для всех CSV-файлов в папке данных."""
    print('Генерация щитов...')
    csv_files = [
        f for f in os.listdir(CONFIG['shields']['data_directory'])
        if f.endswith('.csv')
    ]
    if not csv_files:
        print(f'В папке {CONFIG["shields"]["data_directory"]} '
              'не найдено CSV-файлов.')
        return
    for csv_file in csv_files:
        project_name = os.path.splitext(csv_file)[0]
        shield_target_directory = os.path.join(
            CONFIG['shields']['target_base_directory'], project_name
        )
        shield_html_template_path = os.path.join(
            './html_generator/templates/column_right/shields',
            f'{project_name}.html'
        )
        params = read_params_from_csv(
            os.path.join(CONFIG['shields']['data_directory'], csv_file)
        )
        for title, logo, docs_href in params:
            generate_custom_svg(
                title=title,
                color=CONFIG['shields']['color'],
                logo=logo,
                logo_color=CONFIG['shields']['logo_color'],
                docs_href=docs_href,
                new_height=CONFIG['shields']['new_height'],
                output_directory=shield_target_directory,
                template_path=CONFIG['shields']['template_path'],
                **CONFIG['shields']['scale_factors']
            )
            time.sleep(CONFIG['shields']['time_sleep'])
        generate_shield_template(
            project_name, params, shield_html_template_path
        )


def generate_scripts() -> None:
    """Минифицирует JS-файлы и сохраняет их в выходную директорию."""
    print('Генерация скриптов...')
    process_scripts(
        CONFIG['scripts']['input_directory'],
        CONFIG['scripts']['output_directory']
    )


def generate_css() -> None:
    """Объединяет CSS-файлы и сохраняет минифицированный результат."""
    print('Генерация CSS...')
    css_files = find_css_files(CONFIG['css']['directory'])
    if not css_files:
        print(f'В папке {CONFIG["css"]["directory"]} '
              'не найдено CSS-файлов.')
        return

    minified_css_path = os.path.join(
        CONFIG['css']['target_directory'],
        CONFIG['css']['minified_file']
    )
    combine_and_minify_css(css_files, minified_css_path)


def generate_root_redirect(output_dir: str, default_language: str) -> None:
    """Создаёт корневой index.html с мета-редиректом на язык по умолчанию."""
    redirect_path = f'/{default_language}/'
    content = f"""<!doctype html>
<html lang="{default_language}">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url={redirect_path}">
  <title>Redirecting...</title>
  <script>
    window.location.replace('{redirect_path}');
  </script>
</head>
<body>
  <p>Redirecting to <a href="{redirect_path}">{redirect_path}</a></p>
</body>
</html>
"""
    file_path = os.path.join(output_dir, 'index.html')
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(content)

    print(f'Корневой редирект создан: {file_path}')


def generate_html(mode: str, static_version: str) -> None:
    """Генерирует HTML-страницы для всех языков в заданном режиме (minify/prettier)."""
    print(f'Генерация HTML в режиме {mode}...')
    print(f'Версия статики: {static_version}')

    base_output_dir = CONFIG['html']['output_directory']
    default_language = CONFIG['html']['default_language']

    for lang in CONFIG['html']['languages']:
        lang_output_dir = os.path.join(CONFIG['html']['output_directory'], lang)
        os.makedirs(lang_output_dir, exist_ok=True)

        generate_index_page(
            output_dir=lang_output_dir,
            template_dir=CONFIG['html']['template_directory'],
            index_file=CONFIG['html']['index_file'],
            mode=mode,
            locale=lang,
            static_version=static_version
        )

    generate_root_redirect(base_output_dir, default_language)


def generate_all(args: argparse.Namespace) -> None:
    """Запускает полный цикл генерации: очистка → шилды → JS → CSS → HTML."""
    print('Начинается генерация статических файлов...')
    static_version = str(int(time.time()))
    print(f'Сгенерирована версия статики: {static_version}')

    directories_to_clear = [
        CONFIG['scripts']['output_directory'],
        CONFIG['css']['target_directory'],
    ]

    if args.shields:
        directories_to_clear.append(
            CONFIG['shields']['target_base_directory']
        )

    clear_directories(directories_to_clear)

    if args.shields:
        generate_shields()
    generate_scripts()
    generate_css()
    generate_html(args.html_mode, static_version)
    print('Все файлы успешно сгенерированы.')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Генерация статических файлов.'
    )
    parser.add_argument(
        '--no-shields', action='store_false', dest='shields',
        help='Отключить генерацию щитов.'
    )
    parser.add_argument(
        '--html-mode', choices=['minify', 'prettier'], default='minify',
        help='Режим генерации HTML ("minify" или "prettier").'
    )
    args = parser.parse_args()
    generate_all(args)
