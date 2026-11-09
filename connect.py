"""
connect.py: Conexiones a MongoDB, Cassandra y Dgraph.

Uso:
    python connect.py          # prueba las conexiones a las tres bases de datos
    python connect.py --up     # levanta los contenedores de Docker y luego prueba las conexiones
"""

import os
import shutil
import subprocess
import sys
import time

from pymongo import MongoClient
from pymongo.errors import PyMongoError
from cassandra.cluster import Cluster, NoHostAvailable
import pydgraph


# ---------------------------------------------------------------------------
# Configuracion
# ---------------------------------------------------------------------------

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "travel_platform")

CASSANDRA_HOSTS = os.getenv("CASSANDRA_HOSTS", "127.0.0.1").split(",")
CASSANDRA_PORT = int(os.getenv("CASSANDRA_PORT", "9042"))
CASSANDRA_KEYSPACE = os.getenv("CASSANDRA_KEYSPACE", "travel_platform")
CASSANDRA_REPLICATION_FACTOR = int(os.getenv("CASSANDRA_REPLICATION_FACTOR", "1"))

DGRAPH_URI = os.getenv("DGRAPH_URI", "localhost:9080")

# Contenedores que usa el proyecto
CONTAINERS = [
    {"name": "mongodb", "image": "mongo", "ports": ["27017:27017"]},
    {"name": "node01", "image": "cassandra", "ports": ["9042:9042"]},
    {"name": "dgraph", "image": "dgraph/standalone", "ports": ["8080:8080", "9080:9080"]},
]


# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

def up_containers():
    """Crea o arranca los contenedores de MongoDB, Cassandra y Dgraph."""
    if shutil.which("docker") is None:
        print("[ERROR] Docker no está instalado o no está en el PATH.")
        return

    for c in CONTAINERS:
        status = subprocess.run(
            ["docker", "ps", "-a", "--filter", f"name=^/{c['name']}$", "--format", "{{.Status}}"],
            capture_output=True, text=True,
        ).stdout.strip()

        if not status:
            cmd = ["docker", "run", "-d", "--name", c["name"]]
            for p in c["ports"]:
                cmd += ["-p", p]
            cmd.append(c["image"])
            print(f"Creando contenedor {c['name']} ({c['image']})...")
            subprocess.run(cmd, check=False)
        elif not status.startswith("Up"):
            print(f"Arrancando contenedor {c['name']}...")
            subprocess.run(["docker", "start", c["name"]], check=False)
        else:
            print(f"Contenedor {c['name']} ya está corriendo.")


# ---------------------------------------------------------------------------
# MongoDB
# ---------------------------------------------------------------------------

def get_mongo_db():
    """Regresa (client, db) conectados a MongoDB."""
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    return client, client[MONGO_DB]


# ---------------------------------------------------------------------------
# Cassandra
# ---------------------------------------------------------------------------

def get_cassandra_session(retries=12, wait_seconds=10):
    """
    Regresa (cluster, session) conectados a Cassandra, usando el keyspace del proyecto.
    Cassandra tarda alrededor de un minuto en arrancar, por eso se reintenta.
    """
    for attempt in range(1, retries + 1):
        cluster = Cluster(CASSANDRA_HOSTS, port=CASSANDRA_PORT)
        try:
            session = cluster.connect()
            break
        except NoHostAvailable:
            cluster.shutdown()
            if attempt == retries:
                raise
            print(f"Cassandra aún no responde (intento {attempt}/{retries}), "
                  f"reintentando en {wait_seconds} s...")
            time.sleep(wait_seconds)

    session.execute(
        f"""
        CREATE KEYSPACE IF NOT EXISTS {CASSANDRA_KEYSPACE}
        WITH replication = {{'class': 'SimpleStrategy',
                             'replication_factor': {CASSANDRA_REPLICATION_FACTOR}}}
        """
    )
    session.set_keyspace(CASSANDRA_KEYSPACE)
    return cluster, session


# ---------------------------------------------------------------------------
# Dgraph
# ---------------------------------------------------------------------------

def get_dgraph_client():
    """Regresa (stub, client) conectados a Dgraph por gRPC."""
    stub = pydgraph.DgraphClientStub(DGRAPH_URI)
    client = pydgraph.DgraphClient(stub)
    txn = client.txn(read_only=True)
    try:
        txn.query("{ q(func: has(dgraph.type), first: 1) { uid } }", timeout=5)
    except Exception:
        stub.close()
        raise
    finally:
        txn.discard()
    return stub, client


# ---------------------------------------------------------------------------
# Prueba de conexiones
# ---------------------------------------------------------------------------

def _short_error(e):
    """Mensaje de error corto y legible."""
    if hasattr(e, "details") and callable(e.details):
        return e.details()
    return str(e).splitlines()[0].split(" (configured")[0][:200]


def test_connections():
    """Intenta conectarse a las tres bases de datos e imprime el resultado."""
    ok = True

    try:
        client, db = get_mongo_db()
        print(f"[OK] MongoDB    -> {MONGO_URI} (base de datos: {db.name})")
        client.close()
    except PyMongoError as e:
        ok = False
        print(f"[ERROR] MongoDB -> {MONGO_URI}: {_short_error(e)}")

    try:
        cluster, session = get_cassandra_session()
        print(f"[OK] Cassandra  -> {','.join(CASSANDRA_HOSTS)}:{CASSANDRA_PORT} "
              f"(keyspace: {session.keyspace})")
        cluster.shutdown()
    except Exception as e:
        ok = False
        print(f"[ERROR] Cassandra -> {','.join(CASSANDRA_HOSTS)}:{CASSANDRA_PORT}: {_short_error(e)}")

    try:
        stub, _ = get_dgraph_client()
        print(f"[OK] Dgraph     -> {DGRAPH_URI}")
        stub.close()
    except Exception as e:
        ok = False
        print(f"[ERROR] Dgraph -> {DGRAPH_URI}: {_short_error(e)}")

    if not ok:
        print("\n¿Estan corriendo los contenedores? Puedes levantarlos con: python connect.py --up")
    return ok


if __name__ == "__main__":
    if "--up" in sys.argv:
        up_containers()
        print()
    sys.exit(0 if test_connections() else 1)
