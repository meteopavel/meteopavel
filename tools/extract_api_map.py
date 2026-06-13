"""
Собирает карту Python API по файлу или директории и сохраняет её
в markdown и/или json в директорию project_passport.
Использование:
    python tools/extract_api_map.py app
    python tools/extract_api_map.py app/services/chronicle/prompts.py
    python tools/extract_api_map.py app --project-root .
Опции:
    --format md      Сохранить только markdown
    --format json    Сохранить только json
    --format both    Сохранить markdown и json (по умолчанию)
    --output-dir     Явно указать директорию для артефактов
"""

from __future__ import annotations

import argparse
import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PASSPORT_DIRNAME = 'project_passport'


def parse_args() -> argparse.Namespace:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description='Собирает карту Python API по файлу или директории.',
    )
    parser.add_argument(
        'path',
        help='Путь к Python-файлу или директории относительно project root или абсолютный путь.',
    )
    parser.add_argument(
        '--project-root',
        default='.',
        help='Корень проекта. По умолчанию текущая директория.',
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help=(
            'Директория для выходных файлов. '
            f'По умолчанию <project-root>/{DEFAULT_PASSPORT_DIRNAME}.'
        ),
    )
    parser.add_argument(
        '--format',
        choices=('md', 'json', 'both'),
        default='both',
        help='Формат выходного файла: md, json или both. По умолчанию both.',
    )
    parser.add_argument(
        '--exclude',
        nargs='*',
        default=['.venv', '__pycache__', 'node_modules'],
        help='Имена директорий, которые нужно исключить из сканирования. По умолчанию: .venv __pycache__ node_modules.',
    )
    return parser.parse_args()


def resolve_path(project_root: Path, raw_path: str) -> Path:
    """Разрешает путь относительно project_root, если он не абсолютный."""
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def resolve_output_dir(project_root: Path, raw_output_dir: str | None) -> Path:
    """Определяет директорию для выходных артефактов."""
    if raw_output_dir is None:
        return (project_root / DEFAULT_PASSPORT_DIRNAME).resolve()

    output_dir = Path(raw_output_dir)
    if output_dir.is_absolute():
        return output_dir.resolve()
    return (project_root / output_dir).resolve()


def get_display_path(path: Path, base_dir: Path) -> str:
    """Возвращает путь в виде, удобном для отчёта, по возможности относительно base_dir."""
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def sanitize_filename_part(value: str) -> str:
    """Преобразует строку пути в безопасную часть имени файла."""
    return ''.join(
        character if character.isalnum() or character in ('-', '_') else '_'
        for character in value.strip('/\\')
    )


def build_output_path(
    target_path: Path,
    output_dir: Path,
    base_dir: Path,
    extension: str,
) -> Path:
    """Строит путь к выходному файлу внутри output_dir."""
    display_target = get_display_path(target_path, base_dir)
    normalized_name = sanitize_filename_part(display_target)
    return output_dir / f'api_map__{normalized_name}.{extension}'


def read_and_parse_python_file(file_path: Path) -> tuple[str, ast.Module]:
    """Читает Python-файл и парсит его в AST."""
    source = file_path.read_text(encoding='utf-8')
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        raise ValueError(f'Не удалось распарсить {file_path}: {error}') from error
    return source, tree


def get_docstring_summary(docstring: str | None) -> str | None:
    """Возвращает первую непустую строку докстринга."""
    if not docstring:
        return None
    for line in docstring.strip().splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def format_docstring(docstring: str | None, indent: str = '') -> list[str]:
    """Преобразует докстринг в список строк с заданным отступом."""
    if not docstring:
        return [f'{indent}Нет докстринга.']
    lines = docstring.strip().splitlines()
    return [f'{indent}{line.rstrip()}' for line in lines]


def shorten_text(value: str, limit: int = 100) -> str:
    """Сокращает длинную строку для компактного отображения в markdown."""
    if len(value) <= limit:
        return value
    return value[: limit - 1] + '…'


def has_dataclass_decorator(node: ast.ClassDef) -> bool:
    """Проверяет, помечен ли класс декоратором @dataclass."""
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Name) and decorator.id == 'dataclass':
            return True
        if isinstance(decorator, ast.Attribute) and decorator.attr == 'dataclass':
            return True
        if isinstance(decorator, ast.Call):
            func = decorator.func
            if isinstance(func, ast.Name) and func.id == 'dataclass':
                return True
            if isinstance(func, ast.Attribute) and func.attr == 'dataclass':
                return True
    return False


def format_argument(
    arg: ast.arg,
    default: ast.expr | None = None,
    prefix: str = '',
) -> str:
    """Собирает строковое представление одного аргумента функции."""
    text = f'{prefix}{arg.arg}'
    if arg.annotation is not None:
        text += f': {ast.unparse(arg.annotation)}'
    if default is not None:
        text += f' = {ast.unparse(default)}'
    return text


def get_function_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Собирает строковое представление сигнатуры функции из AST-узла."""
    parts: list[str] = []
    positional_args = list(node.args.posonlyargs) + list(node.args.args)
    positional_defaults = [None] * (len(positional_args) - len(node.args.defaults)) + list(node.args.defaults)
    for index, (arg, default) in enumerate(zip(positional_args, positional_defaults)):
        parts.append(format_argument(arg, default))
        if node.args.posonlyargs and index == len(node.args.posonlyargs) - 1:
            parts.append('/')
    if node.args.vararg:
        parts.append(format_argument(node.args.vararg, prefix='*'))
    elif node.args.kwonlyargs:
        parts.append('*')
    for kwarg, default in zip(node.args.kwonlyargs, node.args.kw_defaults):
        parts.append(format_argument(kwarg, default))
    if node.args.kwarg:
        parts.append(format_argument(node.args.kwarg, prefix='**'))
    signature = f'{node.name}({", ".join(parts)})'
    if node.returns is not None:
        signature += f' -> {ast.unparse(node.returns)}'
    return signature


def get_class_signature(node: ast.ClassDef) -> str:
    """Собирает строковое представление объявления класса."""
    bases = [ast.unparse(base) for base in node.bases]
    signature = node.name
    if bases:
        signature += f'({", ".join(bases)})'
    if has_dataclass_decorator(node):
        signature += ' [dataclass]'
    return signature


def is_constant_name(name: str) -> bool:
    """Проверяет, похоже ли имя на верхнеуровневую константу."""
    return name.isupper()


def extract_constants(tree: ast.Module) -> list[dict[str, Any]]:
    """Извлекает верхнеуровневые константы по эвристике UPPER_CASE."""
    constants: list[dict[str, Any]] = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            value_repr = ast.unparse(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name) and is_constant_name(target.id):
                    constants.append(
                        {
                            'name': target.id,
                            'annotation': None,
                            'value_repr': value_repr,
                            'lineno': getattr(node, 'lineno', None),
                        },
                    )
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and is_constant_name(node.target.id):
                constants.append(
                    {
                        'name': node.target.id,
                        'annotation': ast.unparse(node.annotation) if node.annotation else None,
                        'value_repr': ast.unparse(node.value) if node.value is not None else None,
                        'lineno': getattr(node, 'lineno', None),
                    },
                )
    return constants


def extract_function_data(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    member_kind: str = 'function',
) -> dict[str, Any]:
    """Извлекает структурированную информацию о функции или методе."""
    docstring = ast.get_docstring(node)
    if member_kind == 'method':
        kind = 'async_method' if isinstance(node, ast.AsyncFunctionDef) else 'method'
    else:
        kind = 'async_function' if isinstance(node, ast.AsyncFunctionDef) else 'function'
    return {
        'name': node.name,
        'signature': get_function_signature(node),
        'docstring': docstring,
        'summary': get_docstring_summary(docstring),
        'kind': kind,
        'decorators': [ast.unparse(decorator) for decorator in node.decorator_list],
        'lineno': getattr(node, 'lineno', None),
        'end_lineno': getattr(node, 'end_lineno', None),
    }


def extract_class_fields(node: ast.ClassDef) -> list[dict[str, Any]]:
    """Извлекает поля класса из аннотированных присваиваний на верхнем уровне тела класса."""
    fields: list[dict[str, Any]] = []
    for item in node.body:
        if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
            fields.append(
                {
                    'name': item.target.id,
                    'annotation': ast.unparse(item.annotation) if item.annotation else None,
                    'value_repr': ast.unparse(item.value) if item.value is not None else None,
                    'lineno': getattr(item, 'lineno', None),
                },
            )
    return fields


def extract_class_methods(node: ast.ClassDef) -> list[dict[str, Any]]:
    """Возвращает методы класса верхнего уровня в структурированном виде."""
    methods: list[dict[str, Any]] = []
    for item in node.body:
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
            methods.append(extract_function_data(item, member_kind='method'))

    return methods


def extract_class_data(node: ast.ClassDef) -> dict[str, Any]:
    """Извлекает структурированную информацию о классе."""
    docstring = ast.get_docstring(node)
    fields = extract_class_fields(node)
    methods = extract_class_methods(node)
    is_dataclass = has_dataclass_decorator(node)
    return {
        'name': node.name,
        'signature': get_class_signature(node),
        'docstring': docstring,
        'summary': get_docstring_summary(docstring),
        'kind': 'dataclass' if is_dataclass else 'class',
        'bases': [ast.unparse(base) for base in node.bases],
        'decorators': [ast.unparse(decorator) for decorator in node.decorator_list],
        'fields': fields,
        'methods': methods,
        'lineno': getattr(node, 'lineno', None),
        'end_lineno': getattr(node, 'end_lineno', None),
    }


def extract_python_file_data(file_path: Path, base_dir: Path) -> dict[str, Any]:
    """Извлекает структурированную информацию о Python-файле."""
    _, tree = read_and_parse_python_file(file_path)
    module_docstring = ast.get_docstring(tree)
    classes = [
        extract_class_data(node)
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    ]
    functions = [
        extract_function_data(node, member_kind='function')
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    constants = extract_constants(tree)
    return {
        'path': get_display_path(file_path, base_dir),
        'module_docstring': module_docstring,
        'module_summary': get_docstring_summary(module_docstring),
        'classes': classes,
        'functions': functions,
        'constants': constants,
        'stats': {
            'classes': len(classes),
            'dataclasses': sum(1 for class_data in classes if class_data['kind'] == 'dataclass'),
            'functions': len(functions),
            'methods': sum(len(class_data['methods']) for class_data in classes),
            'constants': len(constants),
        },
    }


def is_meaningful_module(module_data: dict[str, Any]) -> bool:
    """
    Проверяет, содержит ли модуль значимую информацию для карты API.
    Значимыми считаются:
    - модульный докстринг;
    - классы;
    - функции;
    - верхнеуровневые константы.
    """
    return any(
        (
            module_data['module_docstring'],
            module_data['classes'],
            module_data['functions'],
            module_data['constants'],
        ),
    )


def collect_python_file_paths(
    target_path: Path,
    base_dir: Path,
    exclude: list[str] | None = None,
) -> list[Path]:
    """Собирает список Python-файлов из файла или директории, исключая указанные поддиректории."""
    excluded = set(exclude or [])
    if target_path.is_file():
        if target_path.suffix != '.py':
            raise ValueError(f'Ожидался Python-файл: {target_path}')
        return [target_path]
    if target_path.is_dir():
        return sorted(
            (
                file_path
                for file_path in target_path.rglob('*.py')
                if file_path.is_file()
                and not any(part in excluded for part in file_path.parts)
            ),
            key=lambda path: get_display_path(path, base_dir),
        )
    raise ValueError(f'Путь не найден: {target_path}')


def build_api_map_data(
    target_path: Path,
    base_dir: Path,
    exclude: list[str] | None = None,
) -> dict[str, Any]:
    """Собирает структурированную карту API по файлу или директории."""
    all_python_files = collect_python_file_paths(target_path, base_dir, exclude=exclude)
    modules: list[dict[str, Any]] = []
    skipped_files: list[str] = []
    for file_path in all_python_files:
        module_data = extract_python_file_data(file_path, base_dir)
        if is_meaningful_module(module_data):
            modules.append(module_data)
        else:
            skipped_files.append(module_data['path'])
    stats = {
        'modules': len(modules),
        'classes': sum(module['stats']['classes'] for module in modules),
        'dataclasses': sum(module['stats']['dataclasses'] for module in modules),
        'functions': sum(module['stats']['functions'] for module in modules),
        'methods': sum(module['stats']['methods'] for module in modules),
        'constants': sum(module['stats']['constants'] for module in modules),
    }
    return {
        'schema_version': '1.0',
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'generator': 'tools/extract_api_map.py',
        'target': get_display_path(target_path, base_dir),
        'scanned_python_files': len(all_python_files),
        'files_count': len(modules),
        'skipped_files_count': len(skipped_files),
        'skipped_files': skipped_files,
        'stats': stats,
        'modules': modules,
    }


def render_markdown(api_map_data: dict[str, Any]) -> str:
    """Рендерит markdown-версию карты API из структурированных данных."""
    lines = [
        f'# API map: {api_map_data["target"]}',
        '',
        f'Просканировано Python-файлов: {api_map_data["scanned_python_files"]}',
        f'Включено в карту: {api_map_data["files_count"]}',
        f'Пропущено без значимой API-информации: {api_map_data["skipped_files_count"]}',
        '',
        'Сводная статистика:',
        f'- модулей: {api_map_data["stats"]["modules"]}',
        f'- классов: {api_map_data["stats"]["classes"]}',
        f'- dataclass: {api_map_data["stats"]["dataclasses"]}',
        f'- функций: {api_map_data["stats"]["functions"]}',
        f'- методов: {api_map_data["stats"]["methods"]}',
        f'- констант: {api_map_data["stats"]["constants"]}',
    ]
    for module in api_map_data['modules']:
        lines.append('')
        lines.append('---')
        lines.append('')
        lines.append(f'# {module["path"]}')
        if module['module_docstring']:
            lines.append('')
            lines.append('Модуль:')
            lines.extend(format_docstring(module['module_docstring']))
        if module['constants']:
            lines.append('')
            lines.append('Константы:')
            for constant in module['constants']:
                constant_text = constant['name']
                if constant['annotation']:
                    constant_text += f': {constant["annotation"]}'
                if constant['value_repr'] is not None:
                    shortened_value = shorten_text(constant['value_repr'])
                    constant_text += f' = {shortened_value}'
                lines.append(f'- `{constant_text}`')
        if module['classes']:
            lines.append('')
            lines.append('Классы:')
        for class_data in module['classes']:
            lines.append('')
            lines.append(f'- `{class_data["signature"]}`')
            lines.extend(format_docstring(class_data['docstring'], indent='  '))
            if class_data['fields']:
                lines.append('  Поля:')
                for field in class_data['fields']:
                    field_text = field['name']
                    if field['annotation']:
                        field_text += f': {field["annotation"]}'
                    if field['value_repr'] is not None:
                        field_text += f' = {field["value_repr"]}'
                    lines.append(f'  - `{field_text}`')
            if class_data['methods']:
                lines.append('  Методы:')
                for method in class_data['methods']:
                    lines.append(f'  - `{method["signature"]}`')
                    lines.extend(format_docstring(method['docstring'], indent='    '))
        if module['functions']:
            lines.append('')
            lines.append('Функции:')
        for function_data in module['functions']:
            lines.append('')
            lines.append(f'- `{function_data["signature"]}`')
            lines.extend(format_docstring(function_data['docstring'], indent='  '))
    return '\n'.join(lines)


def render_json(api_map_data: dict[str, Any]) -> str:
    """Рендерит JSON-версию карты API из структурированных данных."""
    return json.dumps(api_map_data, ensure_ascii=False, indent=2)


def write_output_files(
    api_map_data: dict[str, Any],
    target_path: Path,
    output_dir: Path,
    base_dir: Path,
    output_format: str,
) -> list[Path]:
    """Сохраняет markdown и/или json версии карты API."""
    output_dir.mkdir(parents=True, exist_ok=True)
    written_files: list[Path] = []
    if output_format in ('md', 'both'):
        markdown_path = build_output_path(target_path, output_dir, base_dir, 'md')
        markdown_path.write_text(render_markdown(api_map_data), encoding='utf-8')
        written_files.append(markdown_path)
    if output_format in ('json', 'both'):
        json_path = build_output_path(target_path, output_dir, base_dir, 'json')
        json_path.write_text(render_json(api_map_data), encoding='utf-8')
        written_files.append(json_path)
    return written_files


def main() -> None:
    """Точка входа: собирает карту API и сохраняет её в выбранных форматах."""
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        raise SystemExit(f'Корень проекта не найден: {project_root}')
    target_path = resolve_path(project_root, args.path)
    output_dir = resolve_output_dir(project_root, args.output_dir)
    if not target_path.exists():
        raise SystemExit(f'Путь не найден: {target_path}')
    api_map_data = build_api_map_data(target_path, project_root, exclude=args.exclude)
    if not api_map_data['modules']:
        raise SystemExit(f'Не найдено подходящих Python-файлов для карты API: {target_path}')
    written_files = write_output_files(
        api_map_data=api_map_data,
        target_path=target_path,
        output_dir=output_dir,
        base_dir=project_root,
        output_format=args.format,
    )
    print('Готово:')
    for output_file in written_files:
        print(f'- {output_file}')


if __name__ == '__main__':
    main()
