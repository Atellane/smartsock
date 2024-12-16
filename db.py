import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from secrets import token_hex
from unittest import TestCase, main
from re import fullmatch
from time import sleep, strftime, localtime


class Db():
    def __init__(self, db_file: str):
        self.__con = self.__create_connection(db_file)
        self.__cur = self.__con.cursor()
        self.reinitialize_database()

    def __create_connection(self, db_file: str) -> sqlite3.Connection:
        """
        hyp:
        create a database connection to a SQLite database
        Return a pointer to the open connection
        """
        con = None
        try:
            con = sqlite3.connect(db_file, check_same_thread=False)
            print(f"{sqlite3.version = }")
        except sqlite3.Error as e:
            print(e)
        return con

    def __create_db(self) -> None:
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
                            dirty BOOL NOT NULL,
                            in_box BOOL NOT NULL,
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

    def __delete_db(self) -> None:
        """
        hyp:
        deletes our project's database
        """
        self.__cur.execute("DROP TABLE IF EXISTS tokens;")
        self.__cur.execute("DROP TABLE IF EXISTS socks;")
        self.__cur.execute("DROP TABLE IF EXISTS users;")
        self.__cur.execute("DROP TABLE IF EXISTS beginning;")
        self.__cur.execute("DROP TABLE IF EXISTS ending;")

    def reinitialize_database(self) -> None:
        """
        hyp:
        recreates a blank database
        """
        self.__delete_db()
        self.__create_db()

    def create_user(self, username: str, password: str) -> None:
        """
        hyp:
        creates user in the users database table
        """
        password = PasswordHasher().hash(password)
        data = {"username": username, "password": password}
        self.__cur.execute("INSERT INTO users VALUES (:username, :password)", data)
        self.__con.commit()

    def connect_user(self, username: str, password: str) -> str:
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

    def disconnect_user(self, username: str, token_auth: str) -> None:
        """
        hyp:
        delete the authentification token from the database to disconnect the user
        """
        data = {"token": token_auth, "user": username}
        self.__cur.execute("DROP TABLE tokens WHERE token=:token AND user=:user", data)

    def create_socks(self, name: str, owner: str, color: str, dirty: bool, in_box: bool) -> None:
        """
        hyp:
        creates sock in the socks database table
        """
        data = {"name": name, "owner": owner, "color": color, "dirty": dirty, "in_box": in_box}
        self.__cur.execute("INSERT INTO socks VALUES (:name, :owner, :color, :dirty, :in_box)", data)
        self.__con.commit()

    def append_usage_history_begin(self, sock: str, owner: str) -> None:
        """
        hyp:
        archive when a socks has been put in the box
        """
        data = {"sock": sock, "owner": owner}
        self.__cur.execute("INSERT INTO beginning (sock, owner) VALUES (:sock, :owner);", data)
        self.__con.commit()
        self.__cur.execute("UPDATE socks SET in_box=TRUE WHERE name=:sock AND owner=:owner", data)

    def append_usage_history_end(self, sock: str, owner: str) -> None:
        """
        hyp:
        archive when a socks has been removed from the box
        """
        data = {"sock": sock, "owner": owner}
        self.__cur.execute("INSERT INTO ending (sock, owner) VALUES (:sock, :owner);", data)
        self.__con.commit()
        self.__cur.execute("UPDATE socks SET in_box=FALSE WHERE name=:sock AND owner=:owner", data)

    def set_dirty(self, sock: str, owner: str, new_val: bool) -> None:
        """
        hyp:
        Change the dirty attribute to new_val
        """
        data = {"sock": sock, "owner": owner, "dirty": new_val}
        self.__cur.execute("UPDATE socks SET dirty=:dirty WHERE name=:sock AND owner=:owner", data)

    def get_all_users(self) -> list:
        """
        hyp:
        returns all informations about all users in the database
        """
        return self.__cur.execute("SELECT * FROM users").fetchall()

    def get_all_socks(self) -> list:
        """
        hyp:
        returns all informations about all socks in the database
        """
        return self.__cur.execute("SELECT * FROM socks").fetchall()

    def get_all_tokens(self) -> list:
        """
        hyp:
        returns all informations about all tokens in the database
        """
        return self.__cur.execute("SELECT * FROM tokens").fetchall()

    def get_all_beginning(self) -> list:
        """
        hyp:
        returns all informations about all the entries in the database table beginning
        """
        return self.__cur.execute("SELECT * FROM beginning").fetchall()

    def get_all_ending(self) -> list:
        """
        hyp:
        returns all informations about all the entries in the database table ending
        """
        return self.__cur.execute("SELECT * FROM ending").fetchall()

    def get_sock_beginning(self, name: str, owner: str) -> list:
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

    def get_sock_ending(self, name: str, owner: str) -> list:
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

    def get_socks_hist_by_color(self, owner: str, color: str) -> list:
        """
        hyp:
        return history for all socks of color <color>
        """
        data = {"owner": owner, "color": color}
        query1 = self.__cur.execute("""SELECT STRFTIME("%d/%m/%Y %H:%M:%S", DATETIME(time, "+1 hour"))
                           AS time_formatted FROM beginning
                           JOIN socks ON socks.name=beginning.sock AND socks.owner=beginning.owner
                           WHERE socks.owner=:owner AND socks.color=:color;""", data).fetchall()
        query2 = self.__cur.execute("""SELECT STRFTIME("%d/%m/%Y %H:%M:%S", DATETIME(time, "+1 hour"))
                           AS ending_formatted FROM ending
                           JOIN socks ON socks.name=ending.sock AND socks.owner=ending.owner
                           WHERE socks.owner=:owner AND socks.color=:color;""", data).fetchall()
        return list(zip(query1, query2))


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

    def test_a(self) -> None:
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

    def test_b(self) -> None:
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

    def test_c(self) -> None:
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

    def test_d(self):
        """
        hyp:
        test if socks are properly created
        """
        name = "testsocks"
        owner = self.user["username"]
        color = ""
        dirty = False 
        in_box = True
        self.db.create_socks(name, owner, color, dirty, in_box)
        self.assertEqual(
                self.db.get_all_socks(),
                [(name, owner, color, dirty, in_box)],
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

    def test_e(self):
        """
        hyp:
        test if socks' states is properly updated
        """
        name = "testsocks"
        owner = self.user["username"]
        self.db.set_dirty(name, owner, True)
        self.assertEqual(self.db.get_all_socks()[0][3], True)

    def test_f(self):
        """
        hyp:
        test if socks' history is correctly fetched by color
        """
        color = "blue"
        self.db.create_socks(color, self.user["username"], color, False, False)
        self.db.append_usage_history_begin(color, self.user["username"])
        query1 = self.db.get_sock_beginning(color, self.user["username"])[0]
        self.assertEqual(
                query1,
                strftime("%d/%m/%Y %H:%M:%S", localtime()),
                "The time when the socks has been put in the box has not been properly archived."
                )
        sleep(2)
        self.db.append_usage_history_end(color, self.user["username"])
        query2 = self.db.get_sock_ending(color, self.user["username"])[0]
        self.assertEqual(
                query2,
                strftime("%d/%m/%Y %H:%M:%S", localtime()),
                "The time when the socks has been put in the box has not been properly archived."
                )
        begin, end = [i[0] for i in self.db.get_socks_hist_by_color(self.user["username"], color)[0]]
        self.assertEqual(
            query1,
            begin,
            "The begin usage history is not properly provided when requesting it by color."
            )
        self.assertEqual(
            query2,
            end,
            "The end usage history is not properly provided when requesting it by color."
            )


if __name__ == '__main__':
    main()
