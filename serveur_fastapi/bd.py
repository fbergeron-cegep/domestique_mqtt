import mariadb
import sys

class BaseDonnees:
    def __init__(self):
        try:
            self.conn = mariadb.connect(
                user="root",
                password="root",
                host="mariadb",
                port=3306,
                database="domestique"
            )
        except mariadb.Error as e:
            print(f"Zut, Un morse m'empêche de profiter de MariaDB: {e}")
            sys.exit(1)

        self.cursor = self.conn.cursor()

        self.creer_bd()


    def creer_bd(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS taches (
            id INT NOT NULL AUTO_INCREMENT,
            nom text NOT NULL,
            due_pour text NOT NULL,
            PRIMARY KEY (id)
            );
        """)
        self.conn.commit()


    def execute(self, req, param=None):
        if param is not None:
            return self.cursor.execute(req, param)
        else:
            return self.cursor.execute(req)

    def fetchall(self):
        return self.cursor.fetchall()

    def fetchone(self):
        return self.cursor.fetchone()

    def commit(self):
        return self.conn.commit()

    def get_last_row_id(self):
        return self.cursor.lastrowid


bd = BaseDonnees()