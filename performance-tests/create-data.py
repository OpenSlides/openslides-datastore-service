import psycopg2
from psycopg2.extras import Json
import random
import string

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="perf",
    user="finn",
    password="finn",
)

# name, #models, #fields per model
collections = (
    ("user", 4000000, 200),
    ("motion", 10000*500, 40),
    ("motion_comment_section", 10000*5, 6),
    ("assignment", 10000*100, 14),
    ("meeting", 10000, 80),
    ("projector", 10000*3, 25),
)
collections = (("user", 100000, 200),)

def r(l):
    return ''.join(random.choice(string.ascii_letters) for i in range(l))

keys = {
    name: [r(16) for _ in range(amount)]
    for name, _, amount in collections
}

def create_user(i):
    user = {
        "id": i,
        "username": "{r(15)}{i}",
    }
    for k in keys["user"]:
        user[k] = str(random.randint(10000,100000000))*2
    return user

def create_model(name):
    model = {
        k: r(16)
        #k: str(random.randint(10000,100000000))*2
        for k in keys[name]
    }
    return model

"""
transaction_size = 100
for name, amount, amount_fields in collections:
    model = create_model(name)
    for block in range(amount//transaction_size):
        offset = block * transaction_size
        with conn:
            with conn.cursor() as cur:
                for i in range(transaction_size):
                    i += offset + 1
                    fqid = f"{name}/{i}"
                    if name == "user":
                        model["username"] = f"{r(15)}{i}"
                    else:
                        del model["username"]
                    cur.execute(
                        "INSERT INTO models(fqid, data) VALUES (%s, %s)",
                        [fqid, Json(model)]
                    )
        print(f"Done {offset + transaction_size} of {name}")
"""

class TheCtx:
    def __init__(self, conn, id):
        self.conn = conn
        self.id = id

# Conn is known globally in the adapter
class MyCtxManager:
    def __init__(self):
        pass

    def __enter__(self):
        self.ctx = TheCtx(conn, r(10))
        print(f"enter {self.ctx.id}")
        back = self.ctx.conn.__enter__()
        print("global conn", conn)
        print("conn enter returned", back)
        return self.ctx

    def __exit__(self, type, value, traceback):
        self.ctx.conn.__exit__(type, value, traceback)
        print("exit")

with MyCtxManager() as ctx:

    # blub

    # somewhere in the adapter
    with ctx.conn.cursor() as cur:
        i = 1
        fqid = f"user/{i}"
        model = create_model("user")
        cur.execute(
            "INSERT INTO models(fqid, data) VALUES (%s, %s)",
            [fqid, Json(model)]
        )


conn.close()
