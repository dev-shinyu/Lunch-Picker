import sqlite3
import datetime

class MenuDB:
    def __init__(self, db_path='menu_data.db'):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS menu_items (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            is_excluded BOOLEAN DEFAULT 0
        )
        """)
        
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS selection_history (
            id INTEGER PRIMARY KEY,
            menu_item_id INTEGER,
            selected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(menu_item_id) REFERENCES menu_items(id)
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
        """)
        self.conn.commit()

    def add_menu_item(self, name):
        try:
            self.cursor.execute(
                "INSERT INTO menu_items (name) VALUES (?)", 
                (name,)
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_menu_items(self):
        self.cursor.execute("SELECT id, name, is_excluded FROM menu_items")
        return self.cursor.fetchall()

    def update_exclusion(self, item_id, is_excluded):
        self.cursor.execute(
            "UPDATE menu_items SET is_excluded = ? WHERE id = ?",
            (int(is_excluded), item_id)
        )
        self.conn.commit()

    def record_selection(self, item_id):
        self.cursor.execute(
            "INSERT INTO selection_history (menu_item_id) VALUES (?)",
            (item_id,)
        )
        self.conn.commit()

    def get_history(self, limit=50):
        self.cursor.execute("""
            SELECT h.id, h.selected_at, m.name 
            FROM selection_history h
            JOIN menu_items m ON h.menu_item_id = m.id
            ORDER BY h.selected_at DESC
            LIMIT ?
        """, (limit,))
        return self.cursor.fetchall()

    def delete_history(self, history_id):
        self.cursor.execute("DELETE FROM selection_history WHERE id = ?", (history_id,))
        self.conn.commit()

    def get_selection_stats(self):
        self.cursor.execute("""
            SELECT m.name, COUNT(h.menu_item_id) as count
            FROM selection_history h
            JOIN menu_items m ON h.menu_item_id = m.id
            GROUP BY m.name
            ORDER BY count DESC
        """)
        return self.cursor.fetchall()

    def get_last_selected_menu(self):
        self.cursor.execute("""
            SELECT m.name
            FROM selection_history h
            JOIN menu_items m ON h.menu_item_id = m.id
            ORDER BY h.selected_at DESC
            LIMIT 1
        """)
        result = self.cursor.fetchone()
        return result[0] if result else None

    def get_setting(self, key):
        self.cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def update_setting(self, key, value):
        self.cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def reset_all_exclusions(self):
        self.cursor.execute("UPDATE menu_items SET is_excluded = 0")
        self.conn.commit()

    def close(self):
        self.conn.close()
