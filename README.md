# Protokoll - Track Your Time
A simple program made for tracking your time spent on tasks per project. Designed around use from the shell.

Installation
============
Using Pip:
```
pip install protokoll
```

Or install from source:
```
git clone https://github.com/metalseargolid/protokoll
cd protokoll
python setup.py install
```

Usage
=====
```
Usage: protokoll [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  project  Commands for working directly with projects.
  task     Commands for working directly with tasks.
```
```
Usage: protokoll project [OPTIONS] COMMAND [ARGS]...

  Commands for working directly with projects.

Options:
  --help  Show this message and exit.

Commands:
  create  Create a new project.
  list    List projects.
  remove  Remove a project.
```
```
Usage: protokoll task [OPTIONS] COMMAND [ARGS]...

  Commands for working directly with tasks.

Options:
  --help  Show this message and exit.

Commands:
  list   List tasks in a given project.
  start  Start a new task in a given project.
  stop   Stop a currently running task.

```

Creating a Project
==================
```
protokoll project create projectname
```

List Existing Projects
======================
```
protokoll project list
```

Starting a Task
===============
*Note*: You may only have one task running at a time.
*Note*: There is a 50 character limit on the task description.
```
protokoll task start projectname "Task Description"
```

Stopping a Task
===============
```
protokoll task stop
```

List All Tasks from Project
===========================
```
protokoll task list projectname
```

Support
=======
If you find this project and feel something is missing, broken, or could otherwise be enhanced,
create an issue on Github and I will look into it when I get a chance.
