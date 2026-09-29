# ==============================================================================
# FILE: src/db_connection.py
# PURPOSE: Manages connections and interactions with the SQLite database.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# A database connection is like a phone call between our Python application and
# the database file. We must establish a connection before reading or writing data,
# and we must close the connection when finished to free system resources.
# ==============================================================================

# Import the built-in 'sqlite3' module to execute SQL commands in Python.
import sqlite3

# Import 'sys' to allow modifying Python's module search path if needed.
import sys

# Import 'os' to verify file existence and manipulate file system paths.
import os

# Import 'contextmanager' from 'contextlib' to create custom 'with' statement handlers.
from contextlib import contextmanager

# Add the project root folder to Python's sys.path so imports work smoothly.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the database path from our central database_config module.
from config.database_config import DB_PATH


def get_db_connection(db_path=DB_PATH):
    """
    Creates and returns a new active connection object to the SQLite database.
    
    Parameters:
        db_path (str): The filesystem path to the SQLite database file.
                       Defaults to DB_PATH defined in config/database_config.py.
                       
    Returns:
        sqlite3.Connection: An active database connection instance.
    """
    # Establish a connection to the SQLite database file at 'db_path'.
    # If the file does not exist, SQLite creates it automatically.
    conn = sqlite3.connect(db_path)
    
    # Configure the connection to return query rows as dictionary-like objects.
    # By default, sqlite3 returns plain tuples (e.g. (1, 'Alice')).
    # 'sqlite3.Row' allows accessing columns by name (e.g. row['user_name']).
    conn.row_factory = sqlite3.Row
    
    # Return the active connection object to the calling function.
    return conn


@contextmanager
def get_db_cursor(db_path=DB_PATH):
    """
    A context manager utility that provides a database cursor using a 'with' block.
    Automatically commits transactions on success and rolls back on failure.
    
    Usage Example:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT * FROM users")
    """
    # Call get_db_connection to create a new database connection object.
    conn = get_db_connection(db_path)
    
    # Create a database cursor object. A cursor is used to send SQL queries to the DB.
    cursor = conn.cursor()
    
    try:
        # Yield the active cursor object to the 'with' block calling code.
        yield cursor
        
        # Commit (save permanently) all database changes made inside the 'with' block.
        conn.commit()
        
    except Exception as error:
        # If any error occurs inside the 'with' block, cancel (rollback) all changes.
        conn.rollback()
        
        # Re-raise the exception so the caller knows an error occurred.
        raise error
        
    finally:
        # Close the connection unconditionally to release file locks and free memory.
        conn.close()


def execute_sql_script(sql_script_string, db_path=DB_PATH):
    """
    Executes multiple SQL statements contained within a single multiline string.
    
    Parameters:
        sql_script_string (str): A string containing one or more SQL commands.
        db_path (str): The filesystem path to the target database.
    """
    # Open a new database connection.
    conn = get_db_connection(db_path)
    
    try:
        # Use 'executescript' to run multiple SQL commands separated by semicolons (;).
        conn.executescript(sql_script_string)
        
        # Commit all table creation or insertion statements.
        conn.commit()
        
    finally:
        # Ensure the connection is always closed after execution finishes.
        conn.close()
