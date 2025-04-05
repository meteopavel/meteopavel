import os

from html_generator.generate_html import generate_index_page
from styles_generator.generate_styles import (
    find_css_files, combine_and_minify_css
)

HTML_OUTPUT_DIRECTORY = '../static'
HTML_TEMPLATE_DIRECTORY = './html_generator/templates'
HTML_INDEX_FILE = 'index.html'

CSS_DIRECTORY = './styles_generator/styles/'
CSS_TARGET_DIRECTORY = '../static/styles/'
MINIFIED_CSS_FILE = 'main.css'


def generate_all():
    """
    Генерирует все статические файлы: HTML и минифицированные стили.
    """
    print('Генерация HTML...')
    generate_index_page(
        output_dir=HTML_OUTPUT_DIRECTORY,
        template_dir=HTML_TEMPLATE_DIRECTORY,
        index_file=HTML_INDEX_FILE,
        mode='minify'
    )

    print('Генерация CSS...')
    css_files = find_css_files(CSS_DIRECTORY)
    if not css_files:
        print(f'В папке {CSS_DIRECTORY} не найдено CSS-файлов.')
    else:
        minified_css_path = os.path.join(
            CSS_TARGET_DIRECTORY, MINIFIED_CSS_FILE
        )
        combine_and_minify_css(css_files, minified_css_path)

    print('Все файлы успешно сгенерированы.')


if __name__ == "__main__":
    generate_all()
