#!/usr/bin/env python3
from setuptools import setup
from io import open # wat da peck?


def read(name):
    with open(name, 'r', encoding='utf-8') as f:
        return f.read()
    
setup(name='tasty_vk',
      version='0.0.2-4',
      description='Python VK api',
      long_description=read('README.md'),
      long_description_content_type='text/markdown',
      author='hatkidchan',
      author_email='hatkidchan@gmail.com',
      url='https://github.com/hatkidchan/tasty_vk',
      packages=['tasty_vk'],
      license='GPL2',
      keywords='vk bot api vkontakte vkapi',
      install_requires=['requests'])

