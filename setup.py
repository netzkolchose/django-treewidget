from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError, RuntimeError):
    long_description = '' 

setup(
    name='django-treewidget',
    packages=find_packages(exclude=['example']),
    include_package_data=True,
    version='0.2.3',
    license='MIT',
    description='treewidget for django admin',
    long_description=long_description,
    author='Joerg Breitbart',
    author_email='j.breitbart@netzkolchose.de',
    url='https://github.com/jerch/django-treewidget',
    download_url='https://github.com/jerch/django-treewidget/archive/0.2.3.tar.gz',
    keywords=['django', 'widget', 'admin', 'tree'],
    classifiers=[],
)
