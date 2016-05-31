from setuptools import setup

__version__='0.0.1' # this is overwritten by the execfile below
exec (open('protokoll/__version__.py').read())

conf=dict(
    name='protokoll',
    description='Track time spent on tasks per project via the CLI',
    url='https://github.com/metalseargolid/protokoll',
    author='Alexander Alber',
    author_email='metalseargolid@gmail.com',
    license='GPLv3',
    keywords=['protokoll', 'time', 'log', 'track', 'timelog', 'timetrack', 'project', 'task'],
    version=__version__,
    packages=['protokoll'],
    entry_points={
        'console_scripts': [
            'protokoll=protokoll.__main__:cli',
            'p=protokoll.__main__:cli'
        ]
    },
    install_requires=[
        "click<6"
    ]
)

conf.update(dict(
    download_url='{0}/tarball/v{1}'.format(conf['url'], conf['version'])
))

setup(**conf)
