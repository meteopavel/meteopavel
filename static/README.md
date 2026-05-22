Примеры генерации статики:
cd source
source ../source/.venv/bin/activate

python generate_static.py
python generate_static.py --no-shields
python generate_static.py --no-shields --html-mode 'prettier'       

Чтобы запустить локально без docker:
cd static
python -m http.server 8000