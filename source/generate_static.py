import os
import time
import argparse

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


def clear_directories(directories):
    """
    Очищает указанные директории.
    """
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


def generate_shields():
    """
    Генерирует щиты (shields) для всех CSV-файлов в папке.
    """
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


def generate_scripts():
    """
    Минифицирует и сохраняет JavaScript-файлы.
    """
    print('Генерация скриптов...')
    process_scripts(
        CONFIG['scripts']['input_directory'],
        CONFIG['scripts']['output_directory']
    )


def generate_css():
    """
    Объединяет и минифицирует CSS-файлы.
    """
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


def generate_html(mode):
    """
    Генерирует HTML-файл.
    :param mode: Режим генерации ('minify' или 'prettier').
    """
    print(f"Генерация HTML в режиме {mode}...")
    generate_index_page(
        output_dir=CONFIG['html']['output_directory'],
        template_dir=CONFIG['html']['template_directory'],
        index_file=CONFIG['html']['index_file'],
        mode=mode
    )


def generate_all(args):
    """
    Главная функция для генерации всех статических файлов.
    """
    print('Начинается генерация статических файлов...')

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
    generate_html(args.html_mode)
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
