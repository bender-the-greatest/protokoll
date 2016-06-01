"""
Entrypoint for Protokoll.
"""

from sys import exit as EXIT

import click
from click import echo

from protokoll.db import Db
from protokoll.exception import ProtokollException
from protokoll.__version__ import __version__ as VERSION


@click.group()
def cli():
    """
    Protokoll CLI. Can be run with either the `protokoll` or `p` commands.
    """
    pass


@cli.command()
def version():
    """
    Display Protokoll version information.
    """
    echo("v{ver}".format(ver=VERSION))

@cli.group()
def project():
    """
    Commands for working directly with projects.
    """
    pass


@project.command()
@click.argument('project_name')
def create(project_name):
    """
    Create a new project.

    If the project already exists, succeed anyways.
    :param project_name: Name of the project.
    """
    try:
        dbo = Db()
        name = dbo.create_project(project_name, close=True)
        echo("Created project '{name}'".format(name=name))
    except ProtokollException as ex:
        echo(str(ex), err=True)
        EXIT(1)


@project.command()
@click.argument('project_name')
def remove(project_name):
    """
    Remove a project.

    WARNING: This will permanently remove all tasks associated with the project.
             There is no confirmation so make sure this is what you want!

    :param project_name: Name of the project to remove.
    """
    try:
        dbo = Db()
        dbo.remove_project(project_name, close=True)
    except ProtokollException as ex:
        echo(str(ex), err=True)
        EXIT(1)


@project.command()
# pylint: disable=W0622
def list():
# pylint: enable=W0622
    """
    List projects.
    """
    try:
        dbo = Db()
        projects = dbo.get_projects(close=True)
    except ProtokollException as ex:
        echo(str(ex), err=True)
        EXIT(1)

    # Format the output nicely
    template = "{project_id: >10}|{name:15}"
    echo(template.format(
        project_id='ID', name='Name'))
    for proj in projects:
        echo(template.format(**proj))


@cli.group()
def task():
    """
    Commands for working directly with tasks.
    """
    pass


@task.command()
@click.argument('project_name')
@click.argument('task_name')
def start(project_name, task_name):
    """
    Start a new task in a given project.

    :param project_name: Name of the project to start the task in.
    :param task_name: Name/Description of the task you are starting. Character limit of 50.
    """
    try:
        dbo = Db()
        dbo.create_task(project_name, task_name[:50], close=True)
    except ProtokollException as ex:
        echo(str(ex), err=True)
        EXIT(1)


@task.command()
def stop():
    """
    Stop a currently running task.
    """
    try:
        dbo = Db()
        dbo.stop_running_task(close=True)
    except ProtokollException as ex:
        echo(str(ex), err=True)
        EXIT(1)


@task.command()
@click.option('-d', '--days', type=click.INT, default=0,
              help='The number of previous days to include in the task list. Must be positive. [0]')
@click.argument('project_name')
# pylint: disable=W0622,E0102
def list(days, project_name):
# pylint: enable=W0622,E0102
    """
    List tasks in a given project.

    :param project_name: Name of the project.
    :type project_name: str
    """
    # Check options
    if days < 0:
        echo('"--days {days}" cannot be less than zero (0).'.format(days=days), err=True)
        EXIT(1)

    try:
        dbo = Db()
        tasks = dbo.get_project_tasks(project_name, days, close=True)
    except ProtokollException as ex:
        echo(str(ex), err=True)
        EXIT(1)

    # Format the output nicely
    template = "{task_id:8}|{project_name:15}|{name:50}|{start_time:20}|{stop_time:20}|" \
      "{total_mins:10}|{is_running:8}"

    echo(template.format(
        task_id='Task Id', project_name='Project Name', name='Task Name', start_time='Start Time', stop_time='Stop Time',
        total_mins='Total Mins', is_running='Is Running'))
    for tsk in tasks:
        echo(template.format(**tsk))


if __name__ == '__main__':
    cli()
