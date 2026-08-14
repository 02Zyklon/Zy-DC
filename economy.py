import json
import os

DB_FILE = "database_golds.json"

def _load_data() -> dict:
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_data(data: dict) -> None:
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_gold(user_id: int) -> int:
    """Retorna o saldo atual de Golds do usuário."""
    data = _load_data()
    uid = str(user_id)
    return data.get(uid, {}).get("gold", 0)

def add_gold(user_id: int, amount: int) -> int:
    """Adiciona Golds ao saldo do usuário e retorna o novo total."""
    data = _load_data()
    uid = str(user_id)
    
    if uid not in data:
        data[uid] = {"gold": 0}
    
    data[uid]["gold"] = data[uid].get("gold", 0) + amount
    _save_data(data)
    return data[uid]["gold"]

def remove_gold(user_id: int, amount: int) -> bool:
    """Remove Golds do usuário se ele tiver saldo suficiente."""
    data = _load_data()
    uid = str(user_id)
    current = data.get(uid, {}).get("gold", 0)
    
    if current < amount:
        return False
        
    data[uid]["gold"] = current - amount
    _save_data(data)
    return True
