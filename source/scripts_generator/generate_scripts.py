import os
from jsmin import jsmin


def minify_script(script_content):
    """
    Минифицирует содержимое JavaScript-файла.
    """
    try:
        return jsmin(script_content)
    except Exception as e:
        print(f'Ошибка при минификации скрипта: {e}')
        return None


def read_script(file_path):
    """
    Читает содержимое JavaScript-файла.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        print(f'Файл {file_path} не найден.')
    except Exception as e:
        print(f'Ошибка при чтении файла {file_path}: {e}')
    return None


def save_minified_script(minified_content, output_path):
    """
    Сохраняет минифицированный скрипт в файл.
    """
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(minified_content)
        print(f'Минифицированный скрипт успешно сохранён: {output_path}')
    except Exception as e:
        print(f'Ошибка при сохранении файла {output_path}: {e}')


def process_scripts(input_directory, output_directory):
    """
    Обрабатывает все JavaScript-файлы в указанной директории:
    минифицирует их и сохраняет в выходную директорию.
    """
    script_files = [
        f for f in os.listdir(input_directory)
        if f.endswith('.js')
    ]
    if not script_files:
        print(f'В папке {input_directory} не найдено JavaScript-файлов.')
        return
    for script_file in script_files:
        input_path = os.path.join(input_directory, script_file)
        output_path = os.path.join(output_directory, script_file)
        script_content = read_script(input_path)
        if not script_content:
            continue
        minified_content = minify_script(script_content)
        if not minified_content:
            continue
        save_minified_script(minified_content, output_path)
