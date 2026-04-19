Примеры генерации статики:
python generate_static.py
python generate_static.py --no-shields
python generate_static.py --no-shields --html-mode 'prettier'       

Чтобы запустить локально без docker:
source ../source/.venv/bin/activate
python -m http.server 8000