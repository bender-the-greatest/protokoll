from protokoll.schema import SCHEMA

import sqlite3
from os import path, makedirs
from sys import stderr
from datetime import datetime

class db:

    def __init__(
            sqlite_dir=path.join(path.expanduser('~'), '.config', 'protokoll'),
            sqlite_filename='protokoll.sqlite3' )
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
        

    def create_project(self, project_name, close=True):
        c = self._sqlite.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS ? "
            "(task_id INT NOT NULL PRIMARY KEY AUTOINCREMENT, "
            "name TEXT, "
            "start_time DATETIME, "
            "stop_time DATETIME, "
            "total_mins INT, "
            "is_running INT NOT NULL)", project_name)
        self._sqlite.commit()
        if close:
            self._sqlite.close()


    def remove_project(self, project_name, close=True):
        """
        Remove a project.

        :param project_name: Name of the project to remove
        :type project_name: str
        :param close: Close the database connection when finished.
        :type close: bool
        """
        
        c = self._sqlite.cursor()
        c.execute("DROP TABLE ? IF EXISTS", project_name)
        self._sqlite.commit()
        if close:
            self._sqlite.close()


    def create_task(self, project_name, task_name="",
                    start_time=datetime.now(), close=True):
        """
        Create a new task in a project. One one task may be running at a time.

        :param project_name: Name of the project to add the task to.
        :type project_name: str
        :param task_name: The name of the task.
        :type task_name: str
        :param start_time: The time the task started.
        :type start_time: datetime
        :return: True on success, False on failure.
        :rtype: bool
        """
        
        c = self._sqlite.cursor()

        try:
            # Check that we do not already have a running task
            if _check_for_running_tasks():
                print('There is already a task running.', file=stderr)
                return False

            # Create the task
            c.execute(
                "INSERT INTO ? "
                "(name, start_time, is_running) "
                "VALUES (?, '?', 1)", project_name, task_name, start_time)
        finally:
            if close:
                self._sqlite.close()
                
            
    def stop_running_task(self, stop_time=datetime.now(), close=True):
        """
        Stop the currently running task.

        :param close: Close the db connection on completion.
        :type close: bool
        :param stop_time: Time that the task was completed.
        :type stop_time: datetime
        :return: True on success, False otherwise.
        :rtype: bool
        """

        c = self._sqlite.cursor()
        for project in _get_projects_with_running_tasks(close=False):
            c.execute(
                "UPDATE ? ",
                "SET stop_time=('?'), is_running=(0) "
                "WHERE is_running=1", project, stop_time)
            
        return True

    def get_projects(self, close=True):
        """
        Gets a list of projects.

        :param close: Whether to close the DB connection or not when finished.
        :type close: bool
        :return: List of project names.
        """
        c = self._sqlite.cursor()
        c.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table'")
        projects = c.fetchall()
        if close:
            self._sqlite.close()
        return projects
        

    def get_project_tasks(self, days=1, close=True):
        pass


    def _check_for_running_tasks(self, close=True):
        """
        Checks for running tasks.

        :return: True if a task is currently running, False if not.
        :rtype: bool
        """
        c = self.sqlite.cursor()
        projects = self.get_projects(close=False)

        try:
            for project in projects:
                c.execute(
                    "SELECT (is_running) FROM ? ",
                    "WHERE is_running=1", project)
                if len(c.fetchall()) > 0:
                    return True

            return False
        finally:
            if close:
                self.sqlite.close()


    def _get_projects_with_running_tasks(self, close=True):
        """
        Return a list of projects with running tasks.

        :param close: Close the db connection on completion.
        :type close: bool
        :return: A list of project names with running tasks.
        :rtype: list (str)
        """
        c = self._sqlite.cursor()
        all_projects = self.get_projects(close=False)
        
        projects = []
        for project in all_projects:
            c.execute(
                "SELECT (is_running) from ? ",
                "WHERE is_running=1", project)
            if len(c.fetchall()) > 0:
                projects.append(project)
        return projects
