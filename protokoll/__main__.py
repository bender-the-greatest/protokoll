import click
from click import echo
from protokoll.db import db


@click.group()
def cli():
    pass


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

    :param project_name: Name of the project.
    """
    dbo = db()
    dbo.create_project(project_name, close=True)


@project.command()
@click.argument('project_name')
def remove(project_name):
    """
    Remove a project.

    WARNING: This will permanently remove all tasks associated with the project.
             There is no confirmation so make sure this is what you want!

    :param project_name: Name of the project to remove.
    """
    dbo = db()
    dbo.remove_project(project_name, close=True)


@project.command()
def list():
    """
    List projects.
    """
    dbo = db()
    for project in dbo.get_projects(close=True):
        echo(project)


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
    dbo = db()
    dbo.create_task(project_name, task_name[:50], close=True)


@task.command()
def stop():
    """
    Stop a currently running task.
    """
    dbo = db()
    dbo.stop_running_task(close=True)
    

@task.command()
@click.option('-d', '--days', type=click.INT, default=0,
             help='The number of previous days to include in the task list. Must be positive. [0]')
@click.argument('project_name')
def list(days, project_name):
    """
    List tasks in a given project.

    :param project_name: Name of the project.
    :type project_name: str
    """
    # Check options
    if days < 0:
        raise ValueError('"days" cannot be less than zero (0).')
    
    dbo = db()
    tasks = dbo.get_project_tasks(project_name, days, close=True)

    # Format the output nicely
    template = "{task_id:8}|{name:50}|{start_time:20}|{stop_time:20}|{total_mins:10}|{is_running:8}"
    echo(template.format(
        task_id='Task Id', name='Name', start_time='Start Time', stop_time='Stop Time',
        total_mins='Total Mins', is_running='Is Running'))
    for task in tasks:
        echo(template.format(**task))

    
if __name__ == '__main__':
    cli()
