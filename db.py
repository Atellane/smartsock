import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from secrets import token_hex
from unittest import TestCase, main
from re import fullmatch
from time import sleep, strftime, localtime


class Db():
    def __init__(self: object, db_file: str) -> object:
        self.__con = self.__create_connection(db_file)
        self.__cur = self.__con.cursor()
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
        self.__cur.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (
                            username TEXT PRIMARY KEY NOT NULL,
                            password TEXT NOT NULL
                          );
                          """)
        self.__cur.execute("""
                         CREATE TABLE IF NOT EXISTS socks
                         (
                            name TEXT NOT NULL,
                            owner TEXT NOT NULL REFERENCES users(username)
                            ON DELETE CASCADE ON UPDATE CASCADE,
                            color TEXT,
                            state TEXT NOT NULL,
                            PRIMARY KEY (name, owner)
                          );
                          """)
        self.__cur.execute("""
                         CREATE TABLE IF NOT EXISTS tokens
                         (
                            token CHAR(32) PRIMARY KEY NOT NULL,
                            user TEXT NOT NULL REFERENCES users(username)
                            ON DELETE CASCADE ON UPDATE CASCADE
                          );
                         """)
        self.__cur.execute("""
                         CREATE TABLE IF NOT EXISTS beginning
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            sock TEXT NOT NULL,
                            owner TEXT NOT NULL,
                            FOREIGN KEY (sock, owner) REFERENCES socks(name, owner)
                            ON DELETE CASCADE ON UPDATE CASCADE
                          );
                         """)
        self.__cur.execute("""
                         CREATE TABLE IF NOT EXISTS ending
                         (
                            id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                            time TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
                            sock TEXT NOT NULL,
                            owner TEXT NOT NULL,
                            FOREIGN KEY (sock, owner) REFERENCES socks(name, owner)
                            ON DELETE CASCADE ON UPDATE CASCADE
                          );
                         """)

    def __delete_db(self: object) -> None:
        """
        hyp:
        deletes our project's database
        """
        self.__cur.execute("DROP TABLE IF EXISTS tokens;")
        self.__cur.execute("DROP TABLE IF EXISTS socks;")
        self.__cur.execute("DROP TABLE IF EXISTS users;")
        self.__cur.execute("DROP TABLE IF EXISTS beginning;")
        self.__cur.execute("DROP TABLE IF EXISTS ending;")

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
        self.__cur.execute("INSERT INTO users VALUES (:username, :password)", data)
        self.__con.commit()

    def connect_user(self: object, username: str, password: str) -> str:
        """
        hyp:
        verify if the password is correct and if so returns the password hash
        uses PasswordHasher which raise an exception when the password is incorrect
        """
        data = (username,)
        passwd_hash = self.__cur.execute("SELECT password FROM users WHERE username = ?", data).fetchone()[0]
        if PasswordHasher().verify(passwd_hash, password):
            token_auth: str = token_hex(32)
            data = {"token": token_auth, "user": username}
            self.__cur.execute("INSERT INTO tokens VALUES (:token, :user)", data)
            self.__con.commit()
            return token_auth

    def disconnect_user(self: object, username: str, token_auth: str) -> None:
        """
        hyp:
        delete the authentification token from the database to disconnect the user
        """
        data = {"token": token_auth, "user": username}
        self.__cur.execute("DROP TABLE tokens WHERE token=:token AND user=:user", data)

    def create_socks(self: object, name: str, owner: str, color: str, state: str) -> None:
        """
        hyp:
        creates sock in the socks database table
        """
        data = {"name": name, "owner": owner, "color": color, "state": state}
        self.__cur.execute("INSERT INTO socks VALUES (:name, :owner, :color, :state)", data)
        self.__con.commit()

    def append_usage_history_begin(self: object, sock: str, owner: str) -> None:
        """
        hyp:
        archive when a socks has been put in the box
        """
        data = {"sock": sock, "owner": owner}
        self.__cur.execute("INSERT INTO beginning (sock, owner) VALUES (:sock, :owner);", data)
        self.__con.commit()

    def append_usage_history_end(self: object, sock: str, owner: str) -> None:
        """
        hyp:
        archive when a socks has been removed from the box
        """
        data = {"sock": sock, "owner": owner}
        self.__cur.execute("INSERT INTO ending (sock, owner) VALUES (:sock, :owner);", data)
        self.__con.commit()

    def get_all_users(self: object) -> list:
        """
        hyp:
        returns all informations about all users in the database
        """
        return self.__cur.execute("SELECT * FROM users").fetchall()

    def get_all_socks(self: object) -> list:
        """
        hyp:
        returns all informations about all socks in the database
        """
        return self.__cur.execute("SELECT * FROM socks").fetchall()

    def get_all_tokens(self: object) -> list:
        """
        hyp:
        returns all informations about all tokens in the database
        """
        return self.__cur.execute("SELECT * FROM tokens").fetchall()

    def get_all_beginning(self: object) -> list:
        """
        hyp:
        returns all informations about all the entries in the database table beginning
        """
        return self.__cur.execute("SELECT * FROM beginning").fetchall()

    def get_all_ending(self: object) -> list:
        """
        hyp:
        returns all informations about all the entries in the database table ending
        """
        return self.__cur.execute("SELECT * FROM ending").fetchall()

    def get_sock_beginning(self: object, name: str, owner: str) -> list:
        """
        hyp:
        returns the list of all the time where a unique sock has been put in the box based on its name and its owner
        """
        data = {"sock": name, "owner": owner}
        query = self.__cur.execute("""SELECT STRFTIME("%d/%m/%Y %H:%M:%S", DATETIME(time, "+1 hour"))
                                AS time_formatee FROM beginning
                                WHERE sock=:sock AND owner=:owner
                                ORDER BY time DESC;""", data).fetchall()
        return [i[0] for i in query]

    def get_sock_ending(self: object, name: str, owner: str) -> list:
        """
        hyp:
        returns the list of all the time where a unique sock has been removed from the box based on its name and its owner
        """
        data = {"sock": name, "owner": owner}
        query = self.__cur.execute("""SELECT STRFTIME("%d/%m/%Y %H:%M:%S", DATETIME(time, "+1 hour"))
                                AS formated_time FROM ending
                                WHERE sock=:sock AND owner=:owner
                                ORDER BY time DESC;""", data).fetchall()
        return [i[0] for i in query]


# les test sont nommés a, b, c, etc car unittest les exécutes dans l'ordre alphabétique
class TestDbMethod(TestCase):
    """test for the Db class"""
    @classmethod
    def setUpClass(cls: type) -> None:
        """
        hyp:
        is called before making any test to work on a single instance of Db
        """
        # Création d'une seule instance de MaClasse pour tous les tests
        cls.db = Db("DBTest.db")
        cls.user = {"username": "test", "password": "test"}
        cls.user1 = {"username": "test1", "password": "test1"}

    def test_a(self: object) -> None:
        """
        hyp:
        test if the database creation has ben properly made
        """
        self.assertEqual(
                self.db.get_all_users(),
                [],
                "There has been some problem(s) during the creation of the users table."
                )

        self.assertEqual(
                self.db.get_all_socks(),
                [],
                "There has been some problem(s) during the creation of the socks table."
                )

        self.assertEqual(
                self.db.get_all_tokens(),
                [],
                "There has been some problem(s) during the creation of the tokens table."
                )

        self.assertEqual(
                self.db.get_all_beginning(),
                [],
                "There has been some problem(s) during the creation of the beginning table."
                )

        self.assertEqual(
                self.db.get_all_ending(),
                [],
                "There has been some problem(s) during the creation of the ending table."
                )

    def test_b(self: object) -> None:
        """
        hyp:
        test if users are properly created
        """
        us_test = {"username": (self.user["username"], self.user1["username"])}
        self.db.create_user(self.user["username"], self.user["password"])
        self.db.create_user(self.user1["username"], self.user1["password"])
        (u1, p1), (u2, p2) = self.db.get_all_users()
        us_pass = [(u1, u2), (p1, p2)] # organise the array as [tuple of username, tuple of password]
        self.assertEqual(
                us_pass[0],
                us_test["username"],
                "There has been some problem whith the creation of the usernames."
                )
        for i in us_pass[1]:
            self.assertTrue(
                    fullmatch(r"^\$argon2id\$v=\d+\$m=\d+,t=\d+,p=\d+\$[A-Za-z0-9+/]{22}\$[A-Za-z0-9+/]{43}$", i),
                    "There has been some problem, the password hash doesn't match the hash pattern."
                    )

    def test_c(self: object) -> None:
        """
        hyp:
        test if the user connection system works properly
        """
        token = self.db.connect_user(self.user1["username"], self.user1["password"])
        self.assertTrue(
                fullmatch(r"^[a-f0-9]{64}$", token),
                "The user's token is not properly generated"
                )
        with self.assertRaises(VerifyMismatchError) as context:
            self.db.connect_user(self.user["username"], "testwrong")

        self.assertTrue(
                "The password does not match the supplied hash" in str(context.exception),
                "The exception is not properly raised."
                )

        self.assertEqual(
                self.db.get_all_tokens()[0][0],
                token,
                "The auth token is not properly saved in the database."
                )

    def test_d(self: object):
        """
        hyp:
        test if socks are properly created
        """
        name = "testsocks"
        owner = self.user["username"]
        color = None
        state = "in the box"
        self.db.create_socks(name, owner, color, state)
        self.assertEqual(
                self.db.get_all_socks(),
                [(name, owner, color, state)],
                "The sock has not been properly created."
                )
        self.db.append_usage_history_begin(name, owner)
        query = self.db.get_sock_beginning(name, owner)[0]
        self.assertEqual(
                query,
                strftime("%d/%m/%Y %H:%M:%S", localtime()),
                "The time when the socks has been put in the box has not been properly archived."
                )
        sleep(2)
        self.db.append_usage_history_end(name, owner)
        query = self.db.get_sock_ending(name, owner)[0]
        self.assertEqual(
                query,
                strftime("%d/%m/%Y %H:%M:%S", localtime()),
                "The time when the socks has been put in the box has not been properly archived."
                )



if __name__ == '__main__':
    main()
