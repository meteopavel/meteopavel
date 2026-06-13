"""HTTP-клиент shields.io: запрос SVG-бейджа и первичный парсинг данных."""
from __future__ import annotations

from typing import Any
from xml.etree import ElementTree as ET

import requests


def fetch_shield_data(title: str, color: str, logo: str, logo_color: str) -> str | None:
    """Выполняет GET-запрос к shields.io и возвращает SVG-контент или None при ошибке."""
    url = (
        f'https://shields.io/badge/{title.replace(" ", "%20")}-{color}'
        f'?logo={logo}&logoColor={logo_color.replace("#", "%23")}'
    )
    try:
        response = requests.get(url)
        response.raise_for_status()

        return response.text
    except requests.exceptions.RequestException as e:
        print(f'Ошибка при выполнении запроса: {e}')
        return None


def parse_svg(svg_content: str) -> dict[str, Any] | None:
    """Парсит SVG-строку и возвращает словарь с размерами, текстами и href изображения."""
    try:
        root = ET.fromstring(svg_content)

        svg_width = root.attrib.get('width')
        svg_height = root.attrib.get('height')

        texts = root.findall('.//{http://www.w3.org/2000/svg}text')
        text_data = []
        for text in texts:
            text_length = text.attrib.get('textLength')
            x = text.attrib.get('x')
            y = text.attrib.get('y')
            text_data.append({'textLength': text_length, 'x': x, 'y': y})

        image = root.find('.//{http://www.w3.org/2000/svg}image')
        svg_image_href = (
            image.attrib.get('href') if image is not None else None
        )
        return {
            'width': svg_width,
            'height': svg_height,
            'texts': text_data,
            'svg_image_href': svg_image_href,
        }
    except ET.ParseError as e:
        print(f'Ошибка при парсинге SVG: {e}')
        return None
