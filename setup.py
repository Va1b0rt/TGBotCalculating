from distutils.core import setup

data_files = [
    ('charset_normalizer', ['./venv/Lib/site-packages/charset_normalizer/__init__.py']),
    ('charset_normalizer.md', ['./venv/Lib/site-packages/charset_normalizer/md.py']),
]

setup(
    windows=['main.py'],
    options={
        'py2exe': {
            'packages': ['aiogram', 'pandas',
                         'cchardet', 'charset_normalizer', 'packaging'],
            'includes': ['aiogram', 'aiogram.dispatcher', 'aiogram.types', 'pandas',
                         'cchardet', 'charset_normalizer'],
            'bundle_files': 1,
        }
    },
    zipfile=None
)
