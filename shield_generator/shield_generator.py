import csv
import string
import time
from shieldsio import fetch_shield_data, parse_svg

NEW_WIDTH_SCALE_FACTOR = 0.9
TEXT_LENGTH_SCALE_FACTOR = 0.85
X_SCALE_FACTOR = 0.87
Y_SCALE_FACTOR = 0.9
DATA_DIRECTORY = './legacy_django_mailer'
DATA_FILE = 'data.csv'
TIME_SLEEP = 1


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


def scale_parameters(parsed_data, new_height=None):
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
            float(original_width) * scale_factor * NEW_WIDTH_SCALE_FACTOR
        )
        new_height = int(new_height)
    else:
        new_width = int(original_width)
        new_height = int(original_height)

    text_data = []
    for text in texts:
        text_length = int(
            float(text['textLength']) * scale_factor * TEXT_LENGTH_SCALE_FACTOR
        )
        x = int(float(text['x']) * scale_factor * X_SCALE_FACTOR)
        y = int(float(text['y']) * scale_factor * Y_SCALE_FACTOR)
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


def save_svg_to_file(template_data, template_path, output_directory, title):
    """
    Сохраняет SVG-файл на основе шаблона и данных.
    """
    with open(template_path, 'r', encoding='utf-8') as template_file:
        svg_template = template_file.read()

    template = string.Template(svg_template)
    svg_code = template.substitute(template_data)

    filename = f'{output_directory}/{title.replace(" ", "_").lower()}.svg'
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(svg_code)

    print(f'SVG файл успешно создан: {filename}')


def generate_custom_svg(title, color, logo, logo_color, docs_href,
                        new_height=None):
    """
    Генерирует SVG с измененными параметрами.
    """
    # Шаг 1: Получение и парсинг данных
    parsed_data = fetch_and_parse_svg(title, color, logo, logo_color)
    if not parsed_data:
        return

    # Шаг 2: Пересчет параметров
    scaled_data = scale_parameters(parsed_data, new_height)

    # Шаг 3: Подготовка данных для шаблона
    template_data = prepare_template_data(title, docs_href, scaled_data)

    # Шаг 4: Сохранение файла
    save_svg_to_file(template_data, 'template.svg', DATA_DIRECTORY, title)


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


if __name__ == '__main__':
    params = read_params_from_csv(f'{DATA_DIRECTORY}/{DATA_FILE}')

    color = 'blue'
    logo_color = '#21e7e7'
    new_height = '30'

    for title, logo, docs_href in params:
        generate_custom_svg(
            title, color, logo, logo_color, docs_href, new_height
        )
        time.sleep(TIME_SLEEP)
