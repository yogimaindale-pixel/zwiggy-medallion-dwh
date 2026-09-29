# ==============================================================================
# FILE: config/database_config.py
# PURPOSE: Central configuration file storing database paths and settings.
# EXPLANATION FOR JUNIOR DEVELOPERS:
# In software engineering, keeping configuration values in one central place
# prevents hardcoding paths throughout the codebase. If the database name or 
# directory path changes in the future, we only need to update this single file.
# ==============================================================================

# Import the 'os' module from Python's standard library.
# The 'os' module allows us to interact with the operating system filesystem,
# such as joining folder paths and creating directories.
import os

# Define the root directory of our project by navigating up from this config folder.
# 'os.path.abspath(__file__)' gives the absolute file path of this file (database_config.py).
# 'os.path.dirname(...)' gets the directory containing this file ('config').
# The outer 'os.path.dirname(...)' gets the parent directory ('zwiggy-medallion-dwh').
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Define the directory path where local SQLite database files will be stored.
# 'os.path.join' combines 'BASE_DIR' and 'data' into a valid path (e.g., /project/data).
DATA_DIR = os.path.join(BASE_DIR, "data")

# Define the directory path where raw JSON sample data files are located.
RAW_DATA_DIR = os.path.join(DATA_DIR, "sample_raw_data")

# Define the filename and full path for our SQLite database file.
# SQLite stores all database tables inside a single local file.
DB_FILENAME = "zwiggy_dwh.db"
DB_PATH = os.path.join(DATA_DIR, DB_FILENAME)

# Define the connection string URL for database engines (e.g., SQLAlchemy or SQLite drivers).
# 'sqlite:///' tells database drivers to connect to a local SQLite file at DB_PATH.
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Define batch processing limits for database bulk insertions.
# Processing data in batches of 100 records prevents memory overload.
BATCH_SIZE = 100

# Define a function to automatically ensure all required data directories exist.
def ensure_directories_exist():
    """
    Creates necessary project folders (e.g., 'data' and 'data/sample_raw_data')
    if they do not already exist on the filesystem.
    """
    # 'os.makedirs' creates the directory specified by DATA_DIR.
    # 'exist_ok=True' prevents Python from throwing an error if the directory already exists.
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # 'os.makedirs' creates the directory specified by RAW_DATA_DIR.
    os.makedirs(RAW_DATA_DIR, exist_ok=True)


# Execute directory verification immediately when this module is imported.
ensure_directories_exist()
