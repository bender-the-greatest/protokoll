"""
Module with helpers for interfacing with the database backend.
"""

import sqlite3
from os import path, makedirs
from datetime import datetime
from click import echo

from protokoll.exception import ProtokollException

class Db:
    """
    Class used to interface with the database.
    """

    def __init__(self,
                 sqlite_dir=path.join(path.expanduser('~'), '.config', 'protokoll'),
                 sqlite_filename='protokoll.sqlite3'):
        """
        Work with the Protokoll SQLite3 database.

        :param sqlite_dir: Path to the directory which is (or will) contain the SQLite3 db.
        :type sqlite_dir: str
        :param sqlite_filename: The name of the SQLite3 db file.
        :type sqlite_filename: str
        """
        # Create directory if it doesn't exist
        if not path.isdir(sqlite_dir):
            makedirs(sqlite_dir)

        fullpath = path.join(sqlite_dir, sqlite_filename)

        # Member vars
        self._sqlite_path = fullpath
        self._sqlite = sqlite3.connect(fullpath)

        # Create the project table if it doesn't exist
        self.__execute(
            "CREATE TABLE IF NOT EXISTS protokoll_projects "
            "(project_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT)", commit=True)

        # Create the tasks table if it doesn't exist
        self.__execute(
            "CREATE TABLE IF NOT EXISTS protokoll_tasks "
            "(task_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "project_id INT, "
            "name TEXT, "
            "start_time DATETIME, "
            "stop_time DATETIME, "
            "total_mins INT, "
            "is_running INT NOT NULL)", commit=True)


    def create_project(self, project_name, close=False):
        """
        Create a new project.

        :param project_name: Name of the new project. Project names cannot start with 'sqlite_'.
        :type project_name: str
        :param close: Close the database connection when completed.
        :type close: bool
        :return: Returns the name of the project on success or if the project already exists.
        :rtype: str
        """
        escaped_name = project_name.replace("'", "''")

        # Make sure the project name is unique, return if it already exists
        results = len(self.__execute(
            "SELECT name FROM protokoll_projects "
            "WHERE name = '{pn}'", pn=escaped_name))
        if results:
            return project_name

        # Add the new project
        self.__execute(
            "INSERT INTO protokoll_projects "
            "(name) "
            "VALUES ('{pn}')", close=close, commit=True, pn=project_name)

        return project_name


    def remove_project(self, project_name, close=False):
        """
        Remove a project and all tasks associated with it.

        :param project_name: Name of the project to remove
        :type project_name: str
        :param close: Close the database connection when finished.
        :type close: bool
        :return: Name of the project which was removed.
        :rtype: str
        """
        project_id = self.__get_project_id(project_name)

        # Remove project
        self.__execute(
            "DELETE FROM protokoll_projects "
            "WHERE project_id = {pid}", commit=True, pid=project_id)

        # Remove associated tasks
        self.__execute(
            "DELETE FROM protokoll_tasks "
            "WHERE project_id = {pid}", close=close, commit=True, pid=project_id)

        return project_name


    def create_task(self, project_name, task_name="",
                    start_time=datetime.now(), close=False):
        """
        Create a new task in a project. Only one task may be running at a time.

        :param project_name: Name of the project to add the task to.
        :type project_name: str
        :param task_name: The name of the task.
        :type task_name: str
        :param start_time: The time the task started.
        :type start_time: datetime
        """

        # Check that we do not already have a running task
        if self.__check_for_running_tasks():
            raise ProtokollException('There is already a task running.')

        # Sanitize single quotes
        task_name = task_name.replace("'", "''")

        # Get project id
        project_id = self.__get_project_id(project_name)

        # Create the task
        self.__execute(
            "INSERT INTO protokoll_tasks "
            "(project_id, name, start_time, is_running) "
            "VALUES ({pid}, '{tn}', DateTime('{start}'), 1)", close=close, commit=True,
            pid=project_id, tn=task_name, start=start_time)


    def stop_running_task(self, stop_time=datetime.now(), close=False):
        """
        Stop any currently running tasks.

        :param close: Close the db connection on completion.
        :type close: bool
        :param stop_time: Time that the task was completed.
        :type stop_time: datetime
        """
        self.__execute(
            "UPDATE protokoll_tasks "
            "SET stop_time=DateTime('{stop}'), is_running=0, "
            "total_mins=Cast(((JulianDay('{stop}') - JulianDay(start_time)) * 24 * 60) AS INT) "
            "WHERE is_running=1", close=close, commit=True, stop=stop_time)


    def get_projects(self, close=False):
        """
        Gets a list of projects.

        :param close: Whether to close the DB connection or not when finished.
        :type close: bool
        :return: List of projects in dict format.
        :rtype: list (dict)
        """
        rows = self.__execute(
            "SELECT * FROM protokoll_projects", close=close)

        projects = []
        for row in rows:
            row_dict = {
                'project_id': row[0] if row[0] is not None else '#',
                'name': row[1] if row[1] else ''
            }
            projects.append(row_dict)
        return projects

    def get_project_tasks(self, project_name, days=0, close=False):
        """
        Retreive a list of project tasks from within a specified number of days.

        :param project_name: Name of the project to retrieve tasks from.
        :type project_name: str
        :param days: How many days worth of tasks you want to retrieve.

                     The value of days is equal to the number of days back to
                     select and return. A value of zero (0) will return tasks
                     only from today, a value of one (1) will return today
                     and yesterdays tasks, a value of two will return tasks
                     from today, yesterday, and the day before, etc.
        :type days: int
        :param close: Close the database connection when completed.
        :type close: bool
        :return: A list of tasks in dict format.
        :rtype: list (dict)
        """
        project_id = self.__get_project_id(project_name)

        rows = self.__execute(
            "SELECT * FROM protokoll_tasks "
            "WHERE Cast((JulianDay('now') - JulianDay(start_time)) AS INT) <= {d} "
            "AND project_id = {pid}", close=close, commit=False, d=days, pid=project_id)

        tasks = []
        for row in rows:
            row_dict = {
                'task_id': row[0] if row[0] is not None else '#',
                'project_name': project_name,
                'name': row[2] if row[2] else '',
                'start_time': row[3] if row[3] is not None else '',
                'stop_time': row[4] if row[4] is not None else '',
                'total_mins': row[5] if row[5] is not None else int((datetime.now() -
                                                                     datetime.strptime(row[3],
                                                                                       "%Y-%m-%d "
                                                                                       "%H:%M:%S"))
                                                                    .total_seconds() / 60),
                'is_running': '' if row[6] == 0 else '*'
            }

            tasks.append(row_dict)

        return tasks


    def __check_for_running_tasks(self, close=False):
        """
        Checks for running tasks.

        :return: True if a task is currently running, False if not.
        :rtype: bool
        """
        result = self.__execute(
            "SELECT is_running FROM protokoll_tasks "
            "WHERE is_running = 1", close=close, commit=False)
        return bool(len(result))


    def __execute(self, cmd, close=False, commit=False, debug=False, **fargs):
        """
        Execute a SQLite3 query, optionally formatted.

        :param cmd: The SQLite3 query to run. Formatting can be applied using the **fargs parameter.
        :type cmd: str
        :param close: Close the connection after the query is run.
        :type close: bool
        :param commit: Commit resulting changes from the query to the database.
        :type commit: bool
        :param debug: Print out the SQL statement prior to execution. Useful only for development.
        :type debug: bool
        :param **fargs: Formatting arguments for the SQLite3 query
        :type **fargs: dict
        """
        error = False
        cursor = self._sqlite.cursor()
        lines = []
        try:
            query = cmd.format(**fargs)
            if debug:
                echo("DEBUG QUERY: {0}".format(query))
            cursor.execute(query)
            lines = cursor.fetchall()
            if commit:
                self._sqlite.commit()
        except Exception:
            error = True
            raise
        finally:
            if error or close:
                self._sqlite.close()

        return lines

    def __get_project_id(self, project_name, close=False):
        """
        Get the project ID of a project.
        Will throw a ProtokollException if the project doesn't exist.

        :param project_name: Name of the project.
        :type project_name: str
        :param close: Close the database connection when done.
        :type: close: bool
        :return: Project ID
        :rtype: int
        """
        # Get the project_id first
        project_id = self.__execute(
            "SELECT project_id from protokoll_projects "
            "WHERE name = '{pn}'", close=close, pn=project_name)
        if not len(project_id):
            raise ProtokollException('Project doesn''t exist')

        for pid in project_id:
            # Get the first element of the tuple
            return pid[0]
