import csv
import os
import subprocess
from jinja2 import Environment, FileSystemLoader

env = Environment(
    loader=FileSystemLoader('templates'),
    lstrip_blocks=True,
    trim_blocks=True
)


def render_template(template_name, context=None):
    """Рендерит шаблон с контекстом."""
    template = env.get_template(template_name)
    if context is None:
        context = {}
    return template.render(context)


def format_with_prettier(file_path):
    """Форматирует файл с помощью Prettier."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f'Файл {file_path} не найден.')

    npx_path = 'C:/Program Files/nodejs/npx.cmd'
    prettier_command = [npx_path, 'prettier', '--write', file_path]

    try:
        subprocess.run(
            prettier_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print('Файл успешно отформатирован с помощью Prettier.')
    except subprocess.CalledProcessError as e:
        print(f'Ошибка при форматировании файла: {e.stderr.decode()}')


def load_links_from_csv(csv_file_path):
    """Загружает данные из CSV-файла."""
    links = []
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            links.append(row)
    return links


def generate_index_page(output_dir):
    """
    Генерирует страницу index.html и сохраняет её в указанную папку.
    """
    rendered_html = render_template('base.html')
    file_path = f'{output_dir}/index.html'
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(rendered_html)
    format_with_prettier(file_path)


if __name__ == '__main__':
    generate_index_page('../static')
