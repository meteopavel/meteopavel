import json
from pathlib import Path


CONTENT_DIR = Path(__file__).resolve().parent


def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)


def normalize_key(file_name):
    return file_name.replace('-', '_')


def load_locale_content(locale='ru'):
    locale_dir = CONTENT_DIR / locale
    if not locale_dir.exists():
        raise FileNotFoundError(f'Директория локали не найдена: {locale_dir}')
    content = {}
    for file_path in locale_dir.glob('*.json'):
        key = normalize_key(file_path.stem)
        content[key] = load_json(file_path)
    return content


def build_context(locale='ru'):
    return load_locale_content(locale)
