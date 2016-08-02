try:
        from setuptools import setup
except:
        from distutils.core import setup

config = {
        'description': 'convert beamer pdf to odp',
        'author': '@peakbook',
        'url': 'No URL',
        'download_url': '',
        'author_email': '',
        'version': '0.1',
        'install_requires': ['docopt','odfpy'],
        'scripts': ['bpdf2odp.py'],
        'name': 'bpdf2odp'
        }

setup(**config)
