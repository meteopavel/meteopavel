import os
import shutil
import subprocess
from htmlmin import minify
from jinja2 import Environment, FileSystemLoader


def render_template(template_name,
                    context=None,
                    template_dir='./html_generator/templates'):
    """Рендерит шаблон с контекстом."""
    env = Environment(
        loader=FileSystemLoader(template_dir),
        lstrip_blocks=True,
        trim_blocks=True
    )
    template = env.get_template(template_name)
    if context is None:
        context = {}
    return template.render(context)


def generate_index_page(output_dir,
                        template_dir,
                        index_file,
                        mode):
    """
    Генерирует страницу index.html.
    """
    os.makedirs(output_dir, exist_ok=True)
    rendered_html = render_template('base.html',
                                    template_dir=template_dir)
    file_path = os.path.join(output_dir, index_file)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(rendered_html)
    if mode == 'prettier':
        format_with_prettier(file_path)
    elif mode == 'minify':
        minify_html(file_path, rendered_html)
    else:
        raise ValueError(f'Неизвестный режим: {mode}. '
                         'Используйте "prettier" или "minify".')


def format_with_prettier(file_path):
    """Форматирует файл с помощью Prettier."""
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


def minify_html(file_path, rendered_html):
    """Минифицирует HTML-файл."""
    minified_html = minify(rendered_html)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(minified_html)
    print('HTML успешно минифицирован.')
