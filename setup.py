from setuptools import setup, find_packages

packages = find_packages(exclude=("auxo_olympus.tests", "auxo_olympus.zmq_examples"))

setup(
      name='auxo_olympus',
      version='0.1',
      author_email='bellabah@mit.edu',
      description='Auxo Olympus Platform',
      packages=packages,
      zip_safe=False,
      install_requires=['pyzmq', 'torch', 'numpy']
)
