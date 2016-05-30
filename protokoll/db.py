import sqlite3
from os import path, makedirs
from datetime import datetime

from click import echo

class db:

    
    ## TODO: Use abstract implementation to allow for pluggable DB backends later
    def __init__(self,
            sqlite_dir=path.join(path.expanduser('~'), '.config', 'protokoll'),
            sqlite_filename='protokoll.sqlite3' ):
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
        

    def create_project(self, project_name, close=False):
        """
        Create a new project.
        
        :param project_name: Name of the new project. Project names cannot start with 'sqlite_'.
        :type project_name: str
        :param close: Close the database connection when completed.
        :type close: bool
        """
        if project_name.startswith('sqlite_'):
            raise ValueError('''Project name cannot start with 'sqlite_'.''')

        project_name = project_name.replace("'", "''")
        
        self.__execute(
            "CREATE TABLE IF NOT EXISTS {tn} "
            "(task_id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT, "
            "start_time DATETIME, "
            "stop_time DATETIME, "
            "total_mins INT, "
            "is_running INT NOT NULL)", close, False, tn=project_name)
        

    def remove_project(self, project_name, close=False):
        """
        Remove a project.

        :param project_name: Name of the project to remove
        :type project_name: str
        :param close: Close the database connection when finished.
        :type close: bool
        """
        self.__execute("DROP TABLE {tn}", close, True, tn=project_name)

    
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
        if self._check_for_running_tasks():
            raise Exception('There is already a task running.')

        # Sanitize single quotes
        task_name = task_name.replace("'", "''")

        # Create the task
        self.__execute(
            "INSERT INTO {tn} "
            "(name, start_time, is_running) "
            "VALUES ('{taskname}', DateTime('{start}'), 1)", close, True,
            tn=project_name, taskname=task_name, start=start_time)

    
    def stop_running_task(self, stop_time=datetime.now(), close=False):
        """
        Stop any currently running tasks.

        :param close: Close the db connection on completion.
        :type close: bool
        :param stop_time: Time that the task was completed.
        :type stop_time: datetime
        """
        for project in self._get_projects_with_running_tasks(close=False):
            self.__execute(
                "UPDATE {tn} "
                "SET stop_time=DateTime('{stop}'), is_running=0, "
                "total_mins=Cast(((JulianDay('{stop}') - JulianDay(start_time)) * 24 * 60) AS INT) " 
                "WHERE is_running=1", close, True, tn=project, stop=stop_time)
    

    def get_projects(self, close=False):
        """
        Gets a list of projects.

        :param close: Whether to close the DB connection or not when finished.
        :type close: bool
        :return: List of project names.
        """
        p_tables = self.__execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite?_%' escape '?'", close=close)

        # Queries return tuples, so grab the first element
        projects = [n[0] for n in p_tables]
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
        rows = self.__execute(
            "SELECT * FROM {tn} "
            "WHERE Cast((JulianDay('now') - JulianDay(start_time)) AS INT) <= {d}", close, False,
            tn=project_name, d=days)
        
        tasks = []
        for row in rows:
            row_dict = {
                'task_id': row[0] if row[0] is not None else '#',
                'name': row[1] if row[1] else '',
                'start_time': row[2] if row[2] is not None else '',
                'stop_time': row[3] if row[3] is not None else '',
                'total_mins': row[4] if row[4] is not None else int((datetime.now() - datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")).total_seconds() / 60),
                'is_running': '' if row[5] == 0 else '*'
            }

            tasks.append(row_dict)
        
        return tasks

    
    def _check_for_running_tasks(self, close=False):
        """
        Checks for running tasks.

        :return: True if a task is currently running, False if not.
        :rtype: bool
        """
        projects = self.get_projects()

        for project in projects:
            rows = self.__execute(
                "SELECT is_running FROM {tn} "
                "WHERE is_running=1", close, False, tn=project)
            if len(rows) > 0:
                return True

        return False

    def _get_projects_with_running_tasks(self, close=False):
        """
        Return a list of projects with running tasks.

        :param close: Close the db connection on completion.
        :type close: bool
        :return: A list of project names with running tasks.
        :rtype: list (str)
        """
        all_projects = self.get_projects()
        
        projects = []
        for project in all_projects:
            rows = self.__execute(
                "SELECT is_running from {tn} "
                "WHERE is_running=1", close, False, tn=project)
                
            if len(rows) > 0:
                projects.append(project)
        return projects
    
    
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
        c = self._sqlite.cursor()
        lines = []
        try:
            query = cmd.format(**fargs)
            if debug:
                echo("DEBUG QUERY: {0}".format(query))
            c.execute(query)
            lines = c.fetchall()
            if commit:
                self._sqlite.commit()
        except Exception:
            error = True
            raise
        finally:
            if error or close:
                self._sqlite.close()

        return lines
            
