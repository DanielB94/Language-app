import sqlite3
import os

def get_connection():
    return sqlite3.connect(os.getenv('DB_NAME', 'mistakes_data.db'))

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # Activates support for foreign keys on SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            language TEXT,
            section TEXT,
            topic TEXT,
            mastered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, language, section, topic)
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mistakes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        language TEXT,
        mistake TEXT,
        correction TEXT,
        frequency INTEGER DEFAULT 1,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        UNIQUE(language, mistake)
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# PROGRESS CRUD
def insert_progress(progress_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    query = '''INSERT INTO progress (user_id, language, section, topic)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, language, section, topic) DO NOTHING'''
               
    cursor.execute(query, progress_data)
    conn.commit()
    conn.close()

def select_progress(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    query = 'SELECT * FROM progress WHERE user_id = ?'
    cursor.execute(query, (user_id,))
    
    result = cursor.fetchall()
    conn.close()
    return result

    def delete_progress(user_id, progress_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    query = 'DELETE FROM progress user_id = ? AND WHERE id = ?'
    cursor.execute(query, (user_id, progress_id))
    
    conn.commit()
    conn.close()


# MISTAKES CRUD
def insert_mistake(mistake_data):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    query = ''''INSERT INTO mistakes (user_id, language, mistake, correction)
    VALUES(?, ?, ?, ?)
    ON CONFLICT(user_id, language, mistake) DO UPDATE SET
        frequency = frequency + 1,
        last_seen = CURRENT_TIMESTAMP
    ''''
    cursor.execute(query, mistake_data)
    conn.commit()
    conn.close()

def select_mistakes(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    query = 'SELECT * FROM mistakes WHERE user_id = ?'
    cursor.execute(query, (user_id,))
    
    result = cursor.fetchall()
    conn.close()

    return result


def delete_mistake(user_id, mistake_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    query = 'DELETE FROM mistakes WHERE id = ? AND user_id = ?'
    cursor.execute(query, (user_id, mistake_id))
    
    conn.commit()
    conn.close()

if __name__ == "__main__": # GUARD OF EXECUTION
    create_tables()