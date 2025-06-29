# ЖКХ-CalculaTor

Счётчик и калькулятор стоимости коммунальных услуг (вода, канализация, электричество).

## Установка

```bash
git clone https://github.com/MrAsavik/jkx_calculator.git
cd jkx_calculator
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py

Использование
Введите текущие показания счётчиков (горячая, холодная вода, электричество).

Нажмите Рассчитать стоимость.

Перейдите на вкладку История для просмотра графиков и таблицы предыдущих расчётов.

Конфигурация
В файле config.json можно менять тарифы и настройки UI без перекомпиляции:


{
  "coefficients": {
    "hot_water": 186.37,
    "cold_water": 41.0,
    "sewage": 28.1,
    "electricity": 4.95
  },
  "ui": {
    "theme": "dark",
    "color_theme": "blue"
  }
}
Разработка
Код оформлен в OOP-стиле, тесты на логику расчётов — через pytest.

Новые фичи и баг-репорты принимаются через раздел Issues на GitHub.

Лицензия
MIT License © 2025 yourname


- Файл `README.md` должен находиться в корне репозитория и служить домашней страницей проекта на GitHub и PyPI :contentReference[oaicite:0]{index=0}.  
- Для корректного отображения на PyPI рекомендуется использовать Markdown (GitHub Flavored) или reStructuredText :contentReference[oaicite:1]{index=1}.  
- README описывает установку, использование, конфигурацию и контакт для поддержки — остальное можно вынести в отдельную документацию (Wiki или Sphinx) :contentReference[oaicite:2]{index=2}.  
- Делайте заголовки, списки, краткие абзацы и по возможности скриншоты, чтобы повысить читабельность :contentReference[oaicite:3]{index=3}.  

---

## Опционально: перенос на `pyproject.toml`

Вместо классического `setup.py` вы можете использовать `pyproject.toml` по PEP 518/517 и PEP 621:

```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "jkx_calculator"
version = "0.1.1"
description = "Счётчик ЖКХ — последняя рабочая версия"
readme = "README.md"
license = { text = "MIT" }
authors = [{ name = "asav" }]
dependencies = [
  "customtkinter",
  "matplotlib",
  "ttkwidgets"
]
requires-python = ">=3.7"
classifiers = [
  "Programming Language :: Python :: 3",
  "License :: OSI Approved :: MIT License",
  "Operating System :: OS Independent"
]
