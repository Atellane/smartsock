import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from secrets import token_hex


class Db():
    def __init__(self: object, db_file: str) -> object:
        self.con = self.__create_connection(db_file)
        self.cur = self.con.cursor()
        self.reinitialize_database()

    def __create_connection(self: object, db_file: str) -> sqlite3.Cursor:
        """
        hyp:
        create a database connection to a SQLite database
        Return a pointer to the open connection
        """
        con = None
        try:
            con = sqlite3.connect(db_file)
            print(f"{sqlite3.version = }")
        except sqlite3.Error as e:
            print(e)
        return con

    def __create_db(self: object) -> None:
        """
        hyp:
        creates our project's database
        """
        self.cur.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (
                            username TEXT PRIMARY KEY NOT NULL,
                            password TEXT NOT NULL
                          );
                          """)
        self.cur.execute("""
                         CREATE TABLE IF NOT EXISTS socks
                         (
                            name TEXT NOT NULL,
                            proprietary TEXT NOT NULL REFERENCES users(username)
                            ON DELETE CASCADE ON UPDATE CASCADE,
                            color TEXT,
                            states TEXT NOT NULL,
                            PRIMARY KEY (name, proprietary)
                          );
                          """)
        self.cur.execute("""
                         CREATE TABLE IF NOT EXISTS tokens
                         (
                            token CHAR(32) PRIMARY KEY NOT NULL,
                            user TEXT NOT NULL REFERENCES users(username)
                            ON DELETE CASCADE ON UPDATE CASCADE
                          );
                         """)
        self.cur.execute("""
                         CREATE TABLE IF NOT EXISTS beginning
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            sock TEXT NOT NULL,
                            proprietary TEXT NOT NULL,
                            FOREIGN KEY (sock, proprietary) REFERENCES socks(name, proprietary)
                            ON DELETE CASCADE ON UPDATE CASCADE
                          );
                         """)
        self.cur.execute("""
                         CREATE TABLE IF NOT EXISTS ending
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            sock TEXT NOT NULL,
                            proprietary TEXT NOT NULL,
                            FOREIGN KEY (sock, proprietary) REFERENCES socks(name, proprietary)
                            ON DELETE CASCADE ON UPDATE CASCADE
                          );
                         """)

    def __delete_db(self: object) -> None:
        """
        hyp:
        deletes our project's database
        """
        self.cur.execute("DROP TABLE IF EXISTS tokens;")
        self.cur.execute("DROP TABLE IF EXISTS socks;")
        self.cur.execute("DROP TABLE IF EXISTS users;")
        self.cur.execute("DROP TABLE IF EXISTS beginning;")
        self.cur.execute("DROP TABLE IF EXISTS ending;")

    def reinitialize_database(self: object) -> None:
        """
        hyp:
        recreates a blank database
        """
        self.__delete_db()
        self.__create_db()

    def create_user(self: object, username: str, password: str) -> None:
        """
        hyp:
        creates user in the users database table
        """
        password = PasswordHasher().hash(password)
        data = {"username": username, "password": password}
        self.cur.execute("INSERT INTO users VALUES (:username, :password)", data)
        self.con.commit()

    def connect_user(self: object, username: str, password: str) -> str:
        """
        hyp:
        verify if the password is correct and if so returns the password hash
        uses PasswordHasher which raise an exception when the password is incorrect
        """
        data = (username,)
        res = self.cur.execute("SELECT password FROM users WHERE username = ?", data)
        passwd_hash = res.fetchone()[0]
        if PasswordHasher().verify(passwd_hash, password):
            token_auth: str = token_hex(32)
            data = {"token": token_auth, "user": username}
            self.cur.execute("INSERT INTO tokens VALUES (:token, :user)", data)
            self.con.commit()
            return token_auth

    def create_socks(self: object, name: str, proprietary: str, color: str, states: str) -> None:
        """
        hyp:
        creates sock in the socks database table
        """
        data = {"name": name, "proprietary": proprietary, "color": color, "states": states}
        self.cur.execute("INSERT INTO socks VALUES (:name, :proprietary, :color, :states)", data)
        self.con.commit()

    def append_usage_history_begin(self: object, sock: str, proprietary: str) -> None:
        """
        hyp:
        archive when a socks has been put in the box
        """
        data = {"sock": sock, "proprietary": proprietary}
        self.cur.execute("INSERT INTO beginning (sock, proprietary) VALUES (:sock, :proprietary);", data)
        self.con.commit()

    def append_usage_history_end(self: object, sock: str, proprietary: str) -> None:
        """
        hyp:
        archive when a socks has been removed from the box
        """
        data = {"sock": sock, "proprietary": proprietary}
        self.cur.execute("INSERT INTO ending (sock, proprietary) VALUES (:sock, :proprietary);", data)
        self.con.commit()


if __name__ == '__main__':
    # open the SQLite database
    db = Db("DBTest.db")
    # make an example request
    print(db.cur.execute("SELECT * FROM users").fetchall())
    # create new users
    user = {"username": "test", "password": "test"}
    user1 = {"username": "test1", "password": "test1"}
    db.create_user(user["username"], user["password"])
    db.create_user(user1["username"], user1["password"])
    # check if new users have been created properly
    print(db.cur.execute("SELECT * FROM users").fetchall())
    # try to connect to user's accounts
    print(db.connect_user(user1["username"], user1["password"]))
    try:
        print(db.connect_user(user["username"], "testwrong"))
    except VerifyMismatchError:
        print("wrong password :(")
    # verify if an authentification token has been properly created
    print(db.cur.execute("SELECT * FROM tokens").fetchall())
    # try to create an example sock
    db.create_socks("testsocks", user["username"], None, "in the box")
    res = db.cur.execute("SELECT * FROM socks").fetchall()
    print(res)
    sock = res[0][0]
    proprietary = res[0][1]
    # try to simulate the archiving of the time where an hypothetic user would put the example sock in the box
    db.append_usage_history_begin(sock, proprietary)
    data = {"sock": sock, "proprietary": proprietary}
    res = db.cur.execute("SELECT * FROM beginning WHERE sock=:sock AND proprietary=:proprietary;", data)
    print(res.fetchall())
    # try to simulate the archiving of the time where an hypothetic user would remove the example sock from the box
    db.append_usage_history_end(sock, proprietary)
    res = db.cur.execute("SELECT * FROM ending WHERE sock=:sock AND proprietary=:proprietary;", data)
    print(res.fetchall())
