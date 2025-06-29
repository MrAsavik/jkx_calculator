from setuptools import setup, find_packages
import pathlib

HERE = pathlib.Path(__file__).parent

setup(
    name='jkx_calculator',
    version='0.1.1',
    description='Счётчик ЖКХ — последняя рабочая версия',
    long_description=(HERE / "README.md").read_text(encoding="utf-8"),
    long_description_content_type="text/markdown",
    author='asav',
    license='MIT',
    url='https://github.com/MrAsavik/jkx_calculator.git',  # ваш репозиторий
    packages=find_packages(exclude=('tests',)),
    install_requires=[
        "customtkinter",
        "matplotlib",
        "ttkwidgets"
    ],
    python_requires='>=3.7',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
