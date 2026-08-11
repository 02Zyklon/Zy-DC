import os
import uvicorn
from fastapi import FastAPI
from threading import Thread

app = FastAPI()

@app.get("/")
def home():
    return {"status": "online", "bot": "Zy-Bot Operacional 100%"}

def run():
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()
