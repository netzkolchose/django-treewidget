from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='django-treewidget',
    packages=find_packages(exclude=['example']),
    include_package_data=True,
    version='0.4.0',
    license='MIT',
    description='treewidget for django admin',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Joerg Breitbart',
    author_email='j.breitbart@netzkolchose.de',
    url='https://github.com/jerch/django-treewidget',
    download_url='https://github.com/jerch/django-treewidget/archive/0.4.0.tar.gz',
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
