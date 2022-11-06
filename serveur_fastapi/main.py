from typing import List

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import paho.mqtt.client as mqtt
import json
import asyncio
from bd import bd

_clients = dict()

### Trucs de MQTT
client_mqtt = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print("Connexion réussie. Message: "+str(rc), flush=True)

    client.subscribe("taches/#")


def on_message(client, userdata, msg):
    print("Reçu: " + msg.topic + " " + str(msg.payload), flush=True)
    hierarchie = msg.topic.split('/')
    if len(hierarchie) > 1:
        uuid = hierarchie[1]
        if uuid in _clients:
            s = _clients[uuid]
            print("Vers le client" + uuid, flush=True)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(s.send_text(str(msg.payload)))
### Trucs de MQTT fin ###


app = FastAPI()


class TacheForm(BaseModel):
    id_client: str
    nom_tache: str
    due_pour: str


class TacheBD(BaseModel):
    id: int
    nom_tache: str
    due_pour: str


@app.on_event("startup")
async def creer_bd():
    client_mqtt.on_connect = on_connect
    client_mqtt.on_message = on_message

    client_mqtt.connect("mqtt", 1883, 60)

    client_mqtt.loop_start()  # On écoute dans un autre fil, pour ne pas bloquer celui-ci
    print("Loop started", flush=True)


@app.get("/", response_class=HTMLResponse)
def root():
    f = open("client_web/index.html", 'r')
    html = f.read()
    return html


@app.post("/api/taches", status_code=201, response_model=TacheBD)
def ajouter_tache(tache: TacheForm):
    bd.execute("INSERT INTO taches(nom, due_pour) VALUES(?, ?)", (tache.nom_tache, tache.due_pour,))
    bd.commit()

    mon_dict = {"nom_tache" : tache.nom_tache, "due_pour": tache.due_pour}
    client_mqtt.publish("taches/" + tache.id_client, json.dumps(mon_dict))
    return recuperer_tache(bd.get_last_row_id())


@app.delete("/api/taches/{id_tache}", response_model=TacheBD)
def retirer_tache(id_tache: int):
    tache = recuperer_tache(id_tache)
    if tache is None:
        raise HTTPException(status_code=404, detail=f"Une tâche ayant l'identifiant {id_tache} n'a pu être trouvée")
    bd.execute("DELETE FROM taches WHERE id = ?", (tache.id,))
    bd.commit()
    return tache


@app.get("/api/taches", response_model=List[TacheBD])
def recuperer_taches():
    bd.execute("SELECT id, nom, due_pour FROM taches")
    tuples_tache = bd.fetchall()
    taches = [TacheBD(id=t[0], nom_tache=t[1], due_pour=t[2]) for t in tuples_tache]
    return taches


@app.get("/api/taches/{id_tache}", response_model=TacheBD)
def recuperer_tache(id_tache: int):
    bd.execute("SELECT id, nom, due_pour FROM taches WHERE id = ?", (id_tache,))
    tuple_tache = bd.fetchone()
    if tuple_tache is None:
        raise HTTPException(status_code=404, detail=f"Une tâche ayant l'identifiant {id_tache} n'a pu être trouvée")
    tache: TacheBD = TacheBD(id=tuple_tache[0], nom_tache=tuple_tache[1], due_pour=tuple_tache[2])
    return tache


@app.websocket("/ws/{uuid}")
async def websocket_endpoint(uuid: str, websocket: WebSocket):
    await websocket.accept()
    _clients[uuid] = websocket
    print(f"Nouveau client de websocket: {uuid}", flush=True)
    while True:
        data = await websocket.receive_text()
        print(f"Message reçu: {data}", flush=True)
        await websocket.send_text(f"Message text was: {data}")
