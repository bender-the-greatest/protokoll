import click

@click.command()
def cli():
    pass


@cli.group()
def project():
    pass


@project.command()
@project.argument('project_name')
def create('project_name'):
    pass


@project.command()
@project.argument('project_name')
def remove('project_name'):
    pass


@project.command()
def list():
    pass


@cli.group()
def task():
    pass


@task.command()
@task.argument('project_name')
@task.argument('task_name')
def start(project_name, task_name):
    pass


@task.command()
def stop():
    pass


@task.command()
def running():
    pass


@task.command()
def list():
    pass


if __name__ == '__main__':
    cli()
