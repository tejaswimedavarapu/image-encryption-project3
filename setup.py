from setuptools import setup, find_packages

setup(
    name='imcrypt',
    version='2.0.0',
    description='A secure image encryption CLI tool using Python cryptography',
    author='theninza',
    author_email='niks.a3198@gmail.com',
    packages=find_packages(),
    install_requires=[
        'cryptography>=41.0.0',
        'Pillow>=10.0.0',
        'click>=8.0.0',
        'tqdm>=4.65.0',
        'colorama>=0.4.6',
    ],
    entry_points={
        'console_scripts': [
            'imcrypt=imcrypt:cli',
        ],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Security :: Cryptography',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
