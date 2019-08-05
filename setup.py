from setuptools import setup, find_packages

packages = [
      'auxo_olympus',
      'auxo_olympus.lib',
      'auxo_olympus.lib.entities',
      'auxo_olympus.lib.services',
      'auxo_olympus.lib.utils'
]

setup(
      name='auxo_olympus',
      version='0.1',
      author_email='bellabah@mit.edu',
      description='Auxo Olympus Platform',
      packages=packages,
      zip_safe=False
)
