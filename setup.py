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
    version='0.3.1',
    license='MIT',
    description='treewidget for django admin',
    long_description=long_description,
    author='Joerg Breitbart',
    author_email='j.breitbart@netzkolchose.de',
    url='https://github.com/jerch/django-treewidget',
    download_url='https://github.com/jerch/django-treewidget/archive/0.3.1.tar.gz',
    keywords=['django', 'widget', 'admin', 'tree'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Database',
        'Topic :: Database :: Front-Ends',
        'Topic :: Software Development :: Libraries',
        'Framework :: Django',
        'Framework :: Django :: 1.11',
        'Framework :: Django :: 2.0',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],
)
