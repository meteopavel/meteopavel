# API map: source

Просканировано Python-файлов: 12
Включено в карту: 7
Пропущено без значимой API-информации: 5

Сводная статистика:
- модулей: 7
- классов: 0
- dataclass: 0
- функций: 35
- методов: 0
- констант: 3

---

# source/content/content_loader.py

Модуль:
Загрузка и агрегация JSON-контента для рендеринга по локали.

Константы:
- `CONTENT_DIR = Path(__file__).resolve().parent`

Функции:

- `load_json(file_path: Path | str) -> Any`
  Загружает JSON-файл и возвращает его содержимое.

- `normalize_key(file_name: str) -> str`
  Преобразует имя файла в ключ контекста (дефис → подчёркивание).

- `load_locale_content(locale: str = 'ru') -> dict[str, Any]`
  Загружает все JSON-файлы локали и возвращает словарь ключ→данные.

- `build_context(locale: str = 'ru') -> dict[str, Any]`
  Возвращает полный контекст рендеринга для указанной локали.

---

# source/generate_static.py

Модуль:
Точка входа генератора статического сайта: HTML, CSS, JS и SVG-шилды.

Константы:
- `SHIELDS_CACHE_PATH = './shields_generator/.shields_cache.json'`
- `CONFIG = {'html': {'output_directory': '../static', 'template_directory': './html_generator/templates', 'ind…`

Функции:

- `_csv_hash(csv_path: str) -> str`
  Нет докстринга.

- `_load_shields_cache() -> dict`
  Нет докстринга.

- `_save_shields_cache(cache: dict) -> None`
  Нет докстринга.

- `_shields_up_to_date(project_name: str, csv_path: str, shield_dir: str, template_path: str, cache: dict) -> bool`
  True если CSV не изменился, все SVG на месте и HTML-шаблон существует.

- `clear_directories(directories: list[str]) -> None`
  Удаляет и пересоздаёт указанные директории.

- `generate_shields() -> None`
  Генерирует SVG-шилды для всех CSV-файлов в папке данных (с кэшем по хэшу CSV).

- `generate_scripts() -> None`
  Минифицирует JS-файлы и сохраняет их в выходную директорию.

- `generate_css() -> None`
  Объединяет CSS-файлы и сохраняет минифицированный результат.

- `generate_root_redirect(output_dir: str, default_language: str) -> None`
  Создаёт корневой index.html с мета-редиректом на язык по умолчанию.

- `generate_html(mode: str, static_version: str) -> None`
  Генерирует HTML-страницы для всех языков в заданном режиме (minify/prettier).

- `generate_all(args: argparse.Namespace) -> None`
  Запускает полный цикл генерации: очистка → шилды → JS → CSS → HTML.

---

# source/html_generator/generate_html.py

Модуль:
Рендеринг Jinja2-шаблонов и постобработка HTML (minify / prettier).

Функции:

- `render_template(template_name: str, context: dict[str, Any] | None = None, template_dir: str = './html_generator/templates') -> str`
  Рендерит Jinja2-шаблон с переданным контекстом и возвращает HTML-строку.

- `generate_index_page(output_dir: str, template_dir: str, index_file: str, mode: str, locale: str = 'ru', static_version: str = '') -> None`
  Рендерит и сохраняет index.html для указанной локали и режима.

- `format_with_prettier(file_path: str) -> None`
  Форматирует HTML-файл через Prettier (требует npx в PATH).

- `minify_html(file_path: str, rendered_html: str) -> None`
  Минифицирует HTML и перезаписывает файл.

---

# source/scripts_generator/generate_scripts.py

Модуль:
Минификация и сохранение JavaScript-файлов через jsmin.

Функции:

- `minify_script(script_content: str) -> str | None`
  Минифицирует JS-строку и возвращает результат или None при ошибке.

- `read_script(file_path: str) -> str | None`
  Читает JS-файл и возвращает его содержимое или None при ошибке.

- `save_minified_script(minified_content: str, output_path: str) -> None`
  Сохраняет минифицированный JS в файл, создавая директории при необходимости.

- `process_scripts(input_directory: str, output_directory: str) -> None`
  Минифицирует все JS-файлы из входной директории и сохраняет в выходную.

---

# source/shields_generator/api/shieldsio.py

Модуль:
HTTP-клиент shields.io: запрос SVG-бейджа и первичный парсинг данных.

Функции:

- `fetch_shield_data(title: str, color: str, logo: str, logo_color: str) -> str | None`
  Выполняет GET-запрос к shields.io и возвращает SVG-контент или None при ошибке.

- `parse_svg(svg_content: str) -> dict[str, Any] | None`
  Парсит SVG-строку и возвращает словарь с размерами, текстами и href изображения.

---

# source/shields_generator/generate_shields.py

Модуль:
Генерация кастомных SVG-шилдов: масштабирование, шаблон, сохранение.

Функции:

- `fetch_and_parse_svg(title: str, color: str, logo: str, logo_color: str) -> dict[str, Any] | None`
  Запрашивает SVG у shields.io и возвращает распарсенные данные или None.

- `scale_parameters(parsed_data: dict[str, Any], new_height: str, width_scale_factor: float, text_length_scale_factor: float, x_scale_factor: float, y_scale_factor: float) -> dict[str, Any]`
  Пересчитывает размеры и координаты SVG с применением коэффициентов масштабирования.

- `prepare_template_data(title: str, docs_href: str, scaled_data: dict[str, Any]) -> dict[str, str]`
  Формирует словарь подстановочных значений для SVG-шаблона.

- `minify_svg(svg_code: str) -> str`
  Удаляет комментарии и лишние пробелы из SVG-строки.

- `save_svg_to_file(template_data: dict[str, str], template_path: str, output_directory: str, title: str) -> None`
  Подставляет данные в SVG-шаблон, минифицирует и сохраняет файл.

- `generate_custom_svg(title: str, color: str, logo: str, logo_color: str, docs_href: str, new_height: str, output_directory: str, template_path: str, width_scale_factor: float, text_length_scale_factor: float, x_scale_factor: float, y_scale_factor: float) -> None`
  Полный цикл генерации одного SVG-шилда: запрос → масштаб → шаблон → файл.

- `read_params_from_csv(file_path: str) -> list[tuple[str, str, str]]`
  Читает CSV с колонками title/logo/docs_href и возвращает список кортежей.

- `generate_shield_template(project_name: str, params: list[tuple[str, str, str]], output_template_path: str) -> None`
  Генерирует статический HTML-фрагмент со шилдами проекта (img в ссылке).

---

# source/styles_generator/generate_styles.py

Модуль:
Поиск, объединение и минификация CSS-файлов.

Функции:

- `find_css_files(directory: str) -> list[str]`
  Рекурсивно находит все CSS-файлы в указанной директории.

- `combine_and_minify_css(input_files: list[str], output_file: str) -> None`
  Объединяет CSS-файлы в один и сохраняет минифицированный результат.