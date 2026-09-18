import sqlite3
import os
import hashlib
import secrets
from typing import Any, List, Optional, Tuple

def get_connection() -> sqlite3.Connection:
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(os.getenv('DB_NAME', 'languages_app.db'))
    # Activates support for foreign keys on SQLite
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def hash_password(password: str) -> str:
    """Generates a random salt and calculates the secure hash for the password using PBKDF2-HMAC.

    Args:
        password: The plain-text password.

    Returns:
        A combined string formatted as 'salt$hash'.
    """
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac(
        'sha256', 
        password.encode('utf-8'), 
        salt.encode('utf-8'), 
        100000
    )
    return f"{salt}${dk.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verifies if a provided password matches the stored one.

    Args:
        stored_password: The 'salt$hash' string saved in the database.
        provided_password: The password entered by the user to validate.

    Returns:
        True if it matches, False otherwise or if a format error occurs.
    """
    try:
        salt, stored_hash = stored_password.split('$')
        dk = hashlib.pbkdf2_hmac(
            'sha256', 
            provided_password.encode('utf-8'), 
            salt.encode('utf-8'), 
            100000
        )
        return dk.hex() == stored_hash
    except ValueError:
        return False

def create_tables() -> None:
    """Creates the main system tables (users, progress, mistakes) if they do not exist."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Progress table (with cascading delete)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                language TEXT,
                section TEXT,
                topic TEXT,
                mastered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, language, section, topic),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Mistakes table (with cascading delete)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS mistakes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            language TEXT,
            mistake TEXT,
            correction TEXT,
            frequency INTEGER DEFAULT 1,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, language, mistake),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")
    finally:
        if conn:
            conn.close()

# USER CRUD
def insert_user(user_data: Tuple[str, str, str]) -> bool:
    """Inserts a new user into the database with a hashed password.

    Args:
        user_data: A tuple containing (user_id, username, raw_password).

    Returns:
        True if successful, False if an error occurred.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        user_id, phone_number, raw_password = user_data
        secure_password_hash = hash_password(raw_password)
        
        query = '''
            INSERT INTO users (id, phone_number, password_hash)
            VALUES (?, ?, ?)
        '''
        cursor.execute(query, (user_id, phone_number, secure_password_hash))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error inserting user: {e}")
        return False
    finally:
        if conn:
            conn.close()

def select_user(user_id: str) -> Optional[Tuple[Any, ...]]:
    """Queries a user by their ID.

    Args:
        user_id: The ID of the user to search for.

    Returns:
        A tuple containing the user data, or None if not found.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM users WHERE id = ?'
        cursor.execute(query, (user_id,))
        
        result = cursor.fetchone()
        return result
    except sqlite3.Error as e:
        print(f"Error querying user: {e}")
        return None
    finally:
        if conn:
            conn.close()

def delete_user(user_id: str) -> bool:
    """Deletes a user by their ID (triggering cascading deletes in related tables).

    Args:
        user_id: The ID of the user to delete.

    Returns:
        True if deleted successfully, False on error.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = 'DELETE FROM users WHERE id = ?'
        cursor.execute(query, (user_id,))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        if conn:
            conn.close()

# PROGRESS CRUD
def insert_progress(progress_data: Tuple[Any, ...]) -> bool:
    """Inserts a progress record avoiding duplicates using ON CONFLICT.

    Args:
        progress_data: A tuple containing (user_id, language, section, topic).

    Returns:
        True if successful, False if an error occurred.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = '''INSERT INTO progress (user_id, language, section, topic)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, language, section, topic) DO NOTHING'''
                
        cursor.execute(query, progress_data)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error inserting progress: {e}")
        return False
    finally:
        if conn:
            conn.close()

def select_progress(user_id: str) -> List[Tuple[Any, ...]]:
    """Retrieves all registered progress for a specific user.

    Args:
        user_id: The ID of the user.

    Returns:
        A list of tuples containing the progress records.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM progress WHERE user_id = ?'
        cursor.execute(query, (user_id,))
        
        result = cursor.fetchall()
        return result
    except sqlite3.Error as e:
        print(f"Error querying progress: {e}")
        return []
    finally:
        if conn:
            conn.close()

def delete_progress(user_id: str, progress_id: int) -> bool:
    """Deletes a specific progress record for a user.

    Args:
        user_id: The ID of the owner user.
        progress_id: The ID of the progress record.

    Returns:
        True if deleted successfully, False on error.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = 'DELETE FROM progress WHERE user_id = ? AND id = ?'
        cursor.execute(query, (user_id, progress_id))
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting progress: {e}")
        return False
    finally:
        if conn:
            conn.close()


# MISTAKES CRUD
def insert_mistake(mistake_data: Tuple[Any, ...]) -> bool:
    """Inserts a mistake or increments its frequency if it already exists (ON CONFLICT).

    Args:
        mistake_data: A tuple containing (user_id, language, mistake, correction).

    Returns:
        True if successful, False if an error occurred.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = '''INSERT INTO mistakes (user_id, language, mistake, correction)
        VALUES(?, ?, ?, ?)
        ON CONFLICT(user_id, language, mistake) DO UPDATE SET
            frequency = frequency + 1,
            last_seen = CURRENT_TIMESTAMP
        '''
        cursor.execute(query, mistake_data)
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error inserting mistake: {e}")
        return False
    finally:
        if conn:
            conn.close()

def select_mistakes(user_id: str) -> List[Tuple[Any, ...]]:
    """Retrieves all stored mistakes for a specific user.

    Args:
        user_id: The ID of the user.

    Returns:
        A list of tuples containing the stored mistakes.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        query = 'SELECT * FROM mistakes WHERE user_id = ?'
        cursor.execute(query, (user_id,))
        
        result = cursor.fetchall()
        return result
    except sqlite3.Error as e:
        print(f"Error querying mistakes: {e}")
        return []
    finally:
        if conn:
            conn.close()



def delete_mistake(user_id: str, mistake_id: int) -> bool:
    """Deletes a specific mistake recorded by the user.

    Args:
        user_id: The ID of the owner user.
        mistake_id: The ID of the mistake to delete.

    Returns:
        True if deleted successfully, False on error.
    """
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        query = 'DELETE FROM mistakes WHERE id = ? AND user_id = ?'
        cursor.execute(query, (user_id, mistake_id))
        
        conn.commit()
        return True
    except sqlite3.Error as e:
        print(f"Error deleting mistake: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__": # GUARD OF EXECUTION
    create_tables()
    print("Database module successfully initialized with types, docstrings, and robust error handling!")