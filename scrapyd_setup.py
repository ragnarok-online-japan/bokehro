from setuptools import setup, find_packages

setup(
    name='project',
    version='1.0',
    packages=find_packages(),
    include_package_data=True,  # 必要なデータを含める
    entry_points={'scrapy': ['settings = bokehro.settings']},
)
