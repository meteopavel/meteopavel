"""
Собирает JSON-файлы паспорта проекта на основе api_map JSON.
Что делает:
1. Читает api_map JSON.
2. Автоматически генерирует project_passport/project.meta.json, если он отсутствует.
3. Собирает project_passport/project.public.json для фронтенда портфолио.
Использование:
    python tools/build_project_passport.py --project-root .
    python tools/build_project_passport.py --project-root . --api-map project_passport/api_map__app.json
    python tools/build_project_passport.py --project-root . --refresh-meta
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_PASSPORT_DIRNAME = 'project_passport'


def parse_args() -> argparse.Namespace:
    """Разбирает аргументы командной строки."""
    parser = argparse.ArgumentParser(
        description='Собирает project.meta.json и project.public.json из api_map JSON.',
    )
    parser.add_argument(
        '--project-root',
        default='.',
        help='Корень проекта. По умолчанию текущая директория.',
    )
    parser.add_argument(
        '--passport-dir',
        default=None,
        help=(
            'Директория паспорта проекта. '
            f'По умолчанию <project-root>/{DEFAULT_PASSPORT_DIRNAME}.'
        ),
    )
    parser.add_argument(
        '--api-map',
        default=None,
        help=(
            'Путь к api_map JSON-файлу. '
            'Если не указан, скрипт попытается автоматически найти его в директории project_passport.'
        ),
    )
    parser.add_argument(
        '--project-id',
        default=None,
        help='Явный project id. Если не задан, будет выведен из имени директории проекта.',
    )
    parser.add_argument(
        '--refresh-meta',
        action='store_true',
        help='Пересоздать project.meta.json даже если он уже существует.',
    )
    return parser.parse_args()


def utc_now_iso() -> str:
    """Возвращает текущее UTC-время в ISO-формате."""
    return datetime.now(timezone.utc).isoformat()


def load_json_file(file_path: Path) -> dict[str, Any]:
    """Загружает JSON-файл в словарь."""
    try:
        return json.loads(file_path.read_text(encoding='utf-8'))
    except FileNotFoundError as error:
        raise SystemExit(f'Файл не найден: {file_path}') from error
    except json.JSONDecodeError as error:
        raise SystemExit(f'Некорректный JSON в файле {file_path}: {error}') from error


def write_json_file(file_path: Path, payload: dict[str, Any]) -> None:
    """Записывает словарь в JSON-файл."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


def resolve_path(project_root: Path, raw_path: str) -> Path:
    """Разрешает путь относительно project_root, если он не абсолютный."""
    path = Path(raw_path)
    if path.is_absolute():
        return path.resolve()
    return (project_root / path).resolve()


def resolve_passport_dir(project_root: Path, raw_passport_dir: str | None) -> Path:
    """Определяет директорию паспорта проекта."""
    if raw_passport_dir is None:
        return (project_root / DEFAULT_PASSPORT_DIRNAME).resolve()
    passport_dir = Path(raw_passport_dir)
    if passport_dir.is_absolute():
        return passport_dir.resolve()
    return (project_root / passport_dir).resolve()


def auto_detect_api_map(passport_dir: Path) -> Path:
    """Пытается автоматически найти api_map JSON в директории паспорта проекта."""
    candidates = sorted(
        path
        for path in passport_dir.glob('api_map__*.json')
        if path.is_file()
    )
    if not candidates:
        raise SystemExit(
            f'В директории {passport_dir} не найдено ни одного api_map JSON-файла. '
            'Сначала запусти extract_api_map.py или укажи --api-map явно.'
        )
    preferred = [path for path in candidates if path.name == 'api_map__app.json']
    if len(preferred) == 1:
        return preferred[0]

    if len(candidates) == 1:
        return candidates[0]
    candidate_names = '\n'.join(f'- {path.name}' for path in candidates)
    raise SystemExit(
        'Найдено несколько api_map JSON-файлов. '
        'Укажи нужный через --api-map.\n'
        f'{candidate_names}'
    )


def path_relative_to_base(path: Path, base: Path) -> str:
    """Возвращает путь относительно base, если это возможно."""
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def slugify(value: str) -> str:
    """Преобразует строку в slug."""
    slug = re.sub(r'[^a-zA-Z0-9]+', '-', value.strip().lower()).strip('-')
    return slug or 'project'


def titleize_slug(slug: str) -> str:
    """Преобразует slug в читаемый title."""
    acronym_map = {
        'api': 'API',
        'cli': 'CLI',
        'llm': 'LLM',
        'docx': 'DOCX',
        'csv': 'CSV',
        'json': 'JSON',
    }
    words = re.split(r'[-_]+', slug)
    title_words = []
    for word in words:
        if not word:
            continue
        lower = word.lower()
        title_words.append(acronym_map.get(lower, lower.capitalize()))
    return ' '.join(title_words) or 'Project'


def join_human_list(items: list[str]) -> str:
    """Собирает список строк в человекочитаемую строку."""
    filtered = [item for item in items if item]
    if not filtered:
        return ''
    if len(filtered) == 1:
        return filtered[0]
    if len(filtered) == 2:
        return f'{filtered[0]} и {filtered[1]}'
    return f'{", ".join(filtered[:-1])} и {filtered[-1]}'


def deep_merge(base: Any, override: Any) -> Any:
    """
    Рекурсивно объединяет структуры.
    Значения из override имеют приоритет.
    Для списков и скаляров override полностью заменяет base.
    """
    if isinstance(base, dict) and isinstance(override, dict):
        merged: dict[str, Any] = dict(base)
        for key, value in override.items():
            if key in merged:
                merged[key] = deep_merge(merged[key], value)
            else:
                merged[key] = value
        return merged
    return override


def collect_text_blobs(api_map_data: dict[str, Any]) -> list[str]:
    """Собирает текстовые фрагменты из api_map для эвристик."""
    blobs: list[str] = []
    for module in api_map_data.get('modules', []):
        blobs.append(module.get('path', ''))
        blobs.append(module.get('module_docstring', '') or '')
        blobs.append(module.get('module_summary', '') or '')
        for constant in module.get('constants', []):
            blobs.append(constant.get('name', ''))
            blobs.append(constant.get('value_repr', '') or '')
        for function_data in module.get('functions', []):
            blobs.append(function_data.get('name', ''))
            blobs.append(function_data.get('signature', ''))
            blobs.append(function_data.get('docstring', '') or '')
        for class_data in module.get('classes', []):
            blobs.append(class_data.get('name', ''))
            blobs.append(class_data.get('signature', ''))
            blobs.append(class_data.get('docstring', '') or '')
            for field in class_data.get('fields', []):
                blobs.append(field.get('name', ''))
                blobs.append(field.get('annotation', '') or '')
            for method_data in class_data.get('methods', []):
                blobs.append(method_data.get('name', ''))
                blobs.append(method_data.get('signature', ''))
                blobs.append(method_data.get('docstring', '') or '')
    return blobs


def detect_features(api_map_data: dict[str, Any]) -> dict[str, bool]:
    """Определяет ключевые особенности проекта по api_map."""
    module_paths = [
        module.get('path', '').lower()
        for module in api_map_data.get('modules', [])
    ]
    text_blob = '\n'.join(collect_text_blobs(api_map_data)).lower()
    has_cli = any(
        path.endswith('/cli.py') or path == 'cli.py' or path == 'app/cli.py'
        for path in module_paths
    )
    has_redmine = 'redmine' in text_blob
    has_documents = 'documents.py' in text_blob or 'docx' in text_blob or 'документ' in text_blob
    has_chronicle = 'chronicle' in text_blob or 'летопис' in text_blob
    has_llm = 'llm' in text_blob or 'prompt' in text_blob
    has_pandas = 'pd.dataframe' in text_blob or 'dataframe' in text_blob or 'pandas' in text_blob
    has_docx = 'docx' in text_blob or 'documenttype' in text_blob or 'paragraph' in text_blob
    has_csv = 'csv' in text_blob
    has_json = 'json' in text_blob
    has_markdown = 'markdown' in text_blob or '.md' in text_blob
    has_env_config = '.env' in text_blob or 'переменн' in text_blob
    has_time_exports = 'time entries' in text_blob or 'timelog' in text_blob or 'трудозатрат' in text_blob
    return {
        'has_cli': has_cli,
        'has_redmine': has_redmine,
        'has_documents': has_documents,
        'has_chronicle': has_chronicle,
        'has_llm': has_llm,
        'has_pandas': has_pandas,
        'has_docx': has_docx,
        'has_csv': has_csv,
        'has_json': has_json,
        'has_markdown': has_markdown,
        'has_env_config': has_env_config,
        'has_time_exports': has_time_exports,
    }


def infer_project_id(project_root: Path, explicit_project_id: str | None) -> str:
    """Определяет project id."""
    if explicit_project_id:
        return slugify(explicit_project_id)
    return slugify(project_root.resolve().name)


def infer_title(project_id: str, features: dict[str, bool]) -> str:
    """Строит читаемый title проекта."""
    if features['has_redmine'] and features['has_documents'] and features['has_chronicle']:
        return 'Redmine Documents & Chronicle Automation'
    if features['has_redmine'] and features['has_documents']:
        return 'Redmine Documents Automation'
    if features['has_redmine'] and features['has_chronicle']:
        return 'Redmine Chronicle Export'
    if features['has_documents'] and features['has_cli']:
        return 'Documents Automation CLI'
    return titleize_slug(project_id)


def infer_tagline(features: dict[str, bool]) -> str:
    """Строит короткий tagline проекта."""
    capabilities: list[str] = []
    if features['has_documents']:
        capabilities.append('генерации документов')
    if features['has_redmine']:
        capabilities.append('экспорта данных из Redmine')
    if features['has_chronicle']:
        capabilities.append('подготовки Chronicle-контекста')
    if features['has_llm']:
        capabilities.append('LLM-friendly prompt workflow')
    if not capabilities:
        return 'Структурированный Python-проект с автоматической технической картой.'
    prefix = 'Python CLI для ' if features['has_cli'] else 'Python-проект для '
    return prefix + join_human_list(capabilities) + '.'


def infer_summary(features: dict[str, bool], api_map_data: dict[str, Any]) -> str:
    """Строит summary проекта."""
    parts: list[str] = []
    if features['has_redmine'] and features['has_time_exports']:
        parts.append('Проект автоматизирует выгрузку трудозатрат и связанных данных из Redmine.')
    if features['has_documents']:
        parts.append('На базе полученных данных формируются DOCX-документы, включая акт и отчёт.')
    if features['has_chronicle'] or features['has_llm']:
        parts.append(
            'Дополнительно проект готовит структурированный контекст задач, '
            "chunk-based prompt-файлы и итоговый prompt для дальнейшего LLM-анализа."
        )
    if features['has_cli']:
        parts.append('Сценарии запуска объединены через единый CLI-слой.')
    if not parts:
        stats = api_map_data.get('stats', {})
        return (
            'Python-проект с формализованной API-картой, пригодной для автоматической '
            f'сборки техпрофиля и портфельного представления. '
            f'В карте: {stats.get("modules", 0)} модулей, '
            f'{stats.get("functions", 0)} функций и {stats.get("classes", 0)} классов.'
        )
    return ' '.join(parts)


def infer_stack(features: dict[str, bool]) -> list[str]:
    """Определяет стек проекта."""
    stack = ['Python']
    if features['has_redmine']:
        stack.append('Redmine API')
    if features['has_pandas']:
        stack.append('pandas')
    if features['has_docx']:
        stack.append('python-docx')
    if features['has_env_config']:
        stack.append('dotenv')
    if features['has_json']:
        stack.append('JSON')
    if features['has_csv']:
        stack.append('CSV')
    if features['has_markdown']:
        stack.append('Markdown')
    return stack


def infer_domain(features: dict[str, bool]) -> list[str]:
    """Определяет доменные теги проекта."""
    domain: list[str] = ['automation']
    if features['has_redmine']:
        domain.append('integrations')
    if features['has_documents']:
        domain.append('document-generation')
    if features['has_time_exports']:
        domain.append('reporting')
    if features['has_cli']:
        domain.append('developer-tools')
    if features['has_chronicle'] or features['has_llm']:
        domain.append('llm-workflows')
    return domain


def infer_highlights(features: dict[str, bool]) -> list[str]:
    """Определяет highlights проекта."""
    highlights: list[str] = []
    if features['has_documents']:
        highlights.append('Генерация актов и отчётов на основе шаблонов DOCX.')
    if features['has_redmine']:
        highlights.append('Интеграция с Redmine API и экспорт данных за выбранный период.')
    if features['has_time_exports']:
        highlights.append('Подготовка CSV-таблиц трудозатрат с итогами по датам и задачам.')
    if features['has_chronicle']:
        highlights.append("Разбиение контекста задач на chunk'и и сборка итогового monthly prompt.")
    if features['has_llm']:
        highlights.append('Подготовка JSON- и markdown-артефактов для последующего LLM-анализа.')
    if features['has_cli']:
        highlights.append('Единый CLI entrypoint для маршрутизации сценариев генерации и экспорта.')
    return highlights


def infer_layers(api_map_data: dict[str, Any]) -> list[str]:
    """Определяет архитектурные слои проекта по путям модулей."""
    layers: list[str] = []
    seen: set[str] = set()
    for module in api_map_data.get('modules', []):
        path = module.get('path', '')
        layer = None
        if path == 'app/cli.py' or path.endswith('/cli.py'):
            layer = 'cli'
        elif path == 'app/config.py' or path.endswith('/config.py'):
            layer = 'config'
        elif '/services/' in path:
            after_services = path.split('/services/', 1)[1]
            parts = after_services.split('/')
            if len(parts) == 1:
                layer = f'services/{parts[0].removesuffix(".py")}'
            else:
                layer = f'services/{parts[0]}'
        elif '/utils/' in path:
            layer = 'utils'
        elif path.startswith('app/'):
            layer = path.removesuffix('.py')

        if layer and layer not in seen:
            seen.add(layer)
            layers.append(layer)
    return layers


def build_feature_flags(features: dict[str, bool]) -> list[str]:
    """Преобразует словарь feature flags в список сигналов."""
    mapping = {
        'has_cli': 'cli_entrypoint',
        'has_redmine': 'redmine_integration',
        'has_documents': 'document_generation',
        'has_chronicle': 'chronicle_workflow',
        'has_llm': 'llm_ready',
        'has_pandas': 'data_processing',
        'has_docx': 'docx_templates',
        'has_csv': 'csv_export',
        'has_json': 'json_artifacts',
        'has_markdown': 'markdown_artifacts',
        'has_env_config': 'env_config',
        'has_time_exports': 'timelog_export',
    }
    return [
        public_name
        for feature_name, public_name in mapping.items()
        if features.get(feature_name)
    ]


def select_key_modules(api_map_data: dict[str, Any], limit: int = 6) -> list[dict[str, Any]]:
    """Выбирает наиболее содержательные модули для короткого техпрофиля."""
    scored_modules: list[tuple[int, dict[str, Any]]] = []
    for module in api_map_data.get('modules', []):
        module_stats = module.get('stats', {})
        score = (
            module_stats.get('functions', 0)
            + module_stats.get('methods', 0)
            + module_stats.get('classes', 0) * 2
            + module_stats.get('constants', 0)
        )
        scored_modules.append((score, module))
    scored_modules.sort(
        key=lambda item: (item[0], item[1].get('path', '')),
        reverse=True,
    )
    result: list[dict[str, Any]] = []
    for _, module in scored_modules[:limit]:
        result.append(
            {
                'path': module.get('path'),
                'summary': module.get('module_summary'),
                'stats': module.get('stats', {}),
            },
        )
    return result


def build_inferred_meta(
    api_map_data: dict[str, Any],
    project_root: Path,
    project_id: str,
) -> dict[str, Any]:
    """Строит автоматически выведенный draft project.meta.json."""
    features = detect_features(api_map_data)
    title = infer_title(project_id, features)
    return {
        'schema_version': '1.0',
        'generated_at': utc_now_iso(),
        'generated_by': 'tools/build_project_passport.py',
        'auto_generated': True,
        'review_status': 'draft',
        'id': project_id,
        'title': title,
        'tagline': infer_tagline(features),
        'summary': infer_summary(features, api_map_data),
        'status': 'active',
        'visibility': 'private_code',
        'role': 'solo_developer',
        'domain': infer_domain(features),
        'stack': infer_stack(features),
        'links': {
            'repo': None,
            'demo': None,
            'details': f'/projects/{project_id}',
        },
        'highlights': infer_highlights(features),
        'public_artifacts': [
            'api_map_json',
            'api_map_markdown',
            'project_meta_json',
            'project_public_json',
        ],
        'notes': {
            'project_root': '.',
            'source_target': api_map_data.get('target'),
            'scanned_python_files': api_map_data.get('scanned_python_files'),
        },
    }


def build_public_payload(
    meta: dict[str, Any],
    api_map_data: dict[str, Any],
    project_root: Path,
    api_map_file: Path,
    meta_file: Path,
    public_file: Path,
) -> dict[str, Any]:
    """Собирает публичный JSON для портфолио."""
    features = detect_features(api_map_data)
    stats = api_map_data.get('stats', {})
    markdown_candidate = api_map_file.with_suffix('.md')
    public_artifacts = {
        'api_map_json': path_relative_to_base(api_map_file, project_root),
        'api_map_markdown': (
            path_relative_to_base(markdown_candidate, project_root)
            if markdown_candidate.exists()
            else None
        ),
        'project_meta_json': path_relative_to_base(meta_file, project_root),
        'project_public_json': path_relative_to_base(public_file, project_root),
    }
    return {
        'schema_version': '1.0',
        'generated_at': utc_now_iso(),
        'generated_by': 'tools/build_project_passport.py',
        'id': meta.get('id'),
        'title': meta.get('title'),
        'tagline': meta.get('tagline'),
        'summary': meta.get('summary'),
        'status': meta.get('status'),
        'visibility': meta.get('visibility'),
        'role': meta.get('role'),
        'domain': meta.get('domain', []),
        'stack': meta.get('stack', []),
        'links': meta.get('links', {}),
        'highlights': meta.get('highlights', []),
        'signals': build_feature_flags(features),
        'tech_profile': {
            'python_files': api_map_data.get('files_count', 0),
            'scanned_python_files': api_map_data.get('scanned_python_files', 0),
            'classes': stats.get('classes', 0),
            'dataclasses': stats.get('dataclasses', 0),
            'functions': stats.get('functions', 0),
            'methods': stats.get('methods', 0),
            'constants': stats.get('constants', 0),
            'has_cli': features['has_cli'],
            'has_redmine_integration': features['has_redmine'],
            'has_document_generation': features['has_documents'],
            'has_llm_workflow': features['has_llm'] or features['has_chronicle'],
            'has_api_map': True,
        },
        'architecture': {
            'target': api_map_data.get('target'),
            'layers': infer_layers(api_map_data),
            'key_modules': select_key_modules(api_map_data),
        },
        'artifacts': public_artifacts,
        'source': {
            'api_map_schema_version': api_map_data.get('schema_version'),
            'api_map_generated_at': api_map_data.get('generated_at'),
            'api_map_generator': api_map_data.get('generator'),
            'meta_auto_generated': meta.get('auto_generated', False),
            'meta_review_status': meta.get('review_status'),
        },
    }


def main() -> None:
    """Точка входа."""
    args = parse_args()
    project_root = Path(args.project_root).resolve()
    if not project_root.exists():
        raise SystemExit(f'Корень проекта не найден: {project_root}')
    passport_dir = resolve_passport_dir(project_root, args.passport_dir)
    passport_dir.mkdir(parents=True, exist_ok=True)
    if args.api_map:
        api_map_file = resolve_path(project_root, args.api_map)
    else:
        api_map_file = auto_detect_api_map(passport_dir)
    if not api_map_file.exists():
        raise SystemExit(f'Файл api_map не найден: {api_map_file}')
    meta_file = passport_dir / 'project.meta.json'
    public_file = passport_dir / 'project.public.json'
    api_map_data = load_json_file(api_map_file)
    project_id = infer_project_id(project_root, args.project_id)
    inferred_meta = build_inferred_meta(
        api_map_data=api_map_data,
        project_root=project_root,
        project_id=project_id,
    )
    if meta_file.exists() and not args.refresh_meta:
        existing_meta = load_json_file(meta_file)
        merged_meta = deep_merge(inferred_meta, existing_meta)
        meta_was_generated = False
    else:
        merged_meta = inferred_meta
        write_json_file(meta_file, merged_meta)
        meta_was_generated = True
    public_payload = build_public_payload(
        meta=merged_meta,
        api_map_data=api_map_data,
        project_root=project_root,
        api_map_file=api_map_file,
        meta_file=meta_file,
        public_file=public_file,
    )
    write_json_file(public_file, public_payload)
    print('Готово:')
    if meta_was_generated:
        print(f'- создан meta: {meta_file}')
    else:
        print(f'- использован существующий meta: {meta_file}')
    print(f'- создан public: {public_file}')


if __name__ == '__main__':
    main()
