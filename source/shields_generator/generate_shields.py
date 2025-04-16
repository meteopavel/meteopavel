import csv
import string
import re
import os
from shields_generator.api.shieldsio import fetch_shield_data, parse_svg


def fetch_and_parse_svg(title, color, logo, logo_color):
    """
    Выполняет запрос к API и парсит SVG-данные.
    """
    svg_content = fetch_shield_data(title, color, logo, logo_color)
    if not svg_content:
        print('Не удалось получить SVG-данные.')
        return None
    parsed_data = parse_svg(svg_content)
    if not parsed_data:
        print('Не удалось распарсить SVG.')
        return None
    return parsed_data


def scale_parameters(parsed_data, new_height,
                     width_scale_factor, text_length_scale_factor,
                     x_scale_factor, y_scale_factor):
    """
    Пересчитывает параметры SVG с учетом масштабирования.
    """
    original_width = parsed_data['width']
    original_height = parsed_data['height']
    texts = parsed_data['texts']
    svg_image_href = parsed_data['svg_image_href']
    scale_factor = 1.0
    if new_height:
        scale_factor = int(new_height) / int(original_height)
        new_width = int(
            float(original_width) * scale_factor * width_scale_factor
        )
        new_height = int(new_height)
    else:
        new_width = int(original_width)
        new_height = int(original_height)
    text_data = []
    for text in texts:
        text_length = int(
            float(text['textLength']) * scale_factor * text_length_scale_factor
        )
        x = int(float(text['x']) * scale_factor * x_scale_factor)
        y = int(float(text['y']) * scale_factor * y_scale_factor)
        text_data.append({
            'textLength': str(text_length),
            'x': str(x),
            'y': str(y),
            'x_offset': str(x + int(15)),
            'y_offset': str(y + int(15)),
        })
    return {
        'width': str(new_width),
        'texts': text_data,
        'svg_image_href': svg_image_href,
    }


def prepare_template_data(title, docs_href, scaled_data):
    """
    Подготавливает данные для подстановки в шаблон.
    """
    return {
        'width': scaled_data['width'],
        'title': title,
        'textLength': scaled_data['texts'][0]['textLength'],
        'x': scaled_data['texts'][0]['x'],
        'x_offset': scaled_data['texts'][0]['x_offset'],
        'y': scaled_data['texts'][0]['y'],
        'y_offset': scaled_data['texts'][0]['y_offset'],
        'docs_href': docs_href,
        'svg_image_href': scaled_data['svg_image_href'] or 'image/svg',
    }


def minify_svg(svg_code):
    """
    Минифицирует SVG-код с помощью регулярных выражений.
    """
    svg_code = re.sub(r'<!--.*?-->', '', svg_code, flags=re.DOTALL)
    svg_code = re.sub(r'\s+', ' ', svg_code)
    svg_code = re.sub(r'\s*([><])\s*', r'\1', svg_code)
    return svg_code


def save_svg_to_file(template_data, template_path, output_directory, title):
    """
    Сохраняет SVG-файл на основе шаблона и данных.
    """
    with open(template_path, 'r', encoding='utf-8') as template_file:
        svg_template = template_file.read()
    template = string.Template(svg_template)
    svg_code = template.substitute(template_data)
    minified_svg = minify_svg(svg_code)
    filename = f'{output_directory}/{title.replace(" ", "_").lower()}.svg'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    filename = f'{output_directory}/{title.replace(" ", "_").lower()}.svg'
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(minified_svg)
    print(f'SVG файл успешно создан и минифицирован: {filename}')


def generate_custom_svg(title, color, logo, logo_color, docs_href,
                        new_height, output_directory, template_path,
                        width_scale_factor, text_length_scale_factor,
                        x_scale_factor, y_scale_factor):
    """
    Генерирует SVG с измененными параметрами.
    """
    # Шаг 1: Получение и парсинг данных
    parsed_data = fetch_and_parse_svg(title, color, logo, logo_color)
    if not parsed_data:
        return
    # Шаг 2: Пересчет параметров
    scaled_data = scale_parameters(
        parsed_data, new_height,
        width_scale_factor, text_length_scale_factor,
        x_scale_factor, y_scale_factor
    )
    # Шаг 3: Подготовка данных для шаблона
    template_data = prepare_template_data(title, docs_href, scaled_data)
    # Шаг 4: Сохранение файла
    save_svg_to_file(template_data, template_path, output_directory, title)


def read_params_from_csv(file_path):
    """
    Читает параметры из CSV-файла и возвращает список кортежей.
    """
    params = []
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                params.append((row['title'], row['logo'], row['docs_href']))
    except FileNotFoundError:
        print(f'Файл {file_path} не найден.')
    except Exception as e:
        print(f'Ошибка при чтении CSV: {e}')
    return params


def generate_shield_template(project_name, params, output_template_path):
    """
    Создает HTML-шаблон для щитов на основе данных из CSV.
    """
    template_content = (
        '<div class="project__shields">\n'
        '  {% set shields = [\n'
    )
    for title, _, _ in params:
        shield_name = f"{title.replace(' ', '_').lower()}.svg"
        template_content += f'    "{shield_name}",\n'
    template_content += (
        '  ] %}\n'
        '  \n'
        '  {% for shield in shields %}\n'
        f'    <object\n'
        f'      type="image/svg+xml"\n'
        f'      data-src="./images/shields/{project_name}/{{{{ shield }}}}"\n'
        '       class="lazy-object"'
        '    ></object>\n'
        '  {% endfor %}\n'
        '</div>'
    )
    os.makedirs(os.path.dirname(output_template_path), exist_ok=True)
    with open(output_template_path, 'w', encoding='utf-8') as file:
        file.write(template_content)
    print(f'Шаблон для щитов успешно создан: {output_template_path}')
