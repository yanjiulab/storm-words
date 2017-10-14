# coding:utf-8

from setuptools import setup, find_packages
import sys

for p in sys.path:
    print(p, ',')

setup(name='stormwords',
      version='0.0.1',
      description="基于头脑风暴的英语学习小工具",
      long_description="""基于有道API和有道词典web版的在terminal查询词的小工具,详情请见github""",
      keywords='python youdao dictionary terminal',
      author='liyanjiu',
      author_email='liyanjiu@outlook.com',
      url='https://github.com/liyanjiu/stormwords',
      license='MIT',
      packages=find_packages(exclude=['tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'termcolor'
      ],
      classifiers=[
          'Programming Language :: Python :: 3.5',

      ],
      entry_points={
          'console_scripts': [
              'sw=stormwords.main:main',
          ]
      },
)
