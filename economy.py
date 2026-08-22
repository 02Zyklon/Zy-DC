import json
import os
import asyncio
import logging

CAMINHO_BANCO = "database_golds.json"
_lock = asyncio.Lock()

# --- FUNÇÕES AUXILIARES DE LEITURA E ESCRITA ---

def _carregar_dados_raw() -> dict:
    if not os.path.exists(CAMINHO_BANCO):
        with open(CAMINHO_BANCO, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
    try:
        with open(CAMINHO_BANCO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"⚠️ Erro ao ler {CAMINHO_BANCO}: {e}")
        return {}

def _salvar_dados_raw(dados: dict):
    try:
        with open(CAMINHO_BANCO, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"⚠️ Erro ao salvar {CAMINHO_BANCO}: {e}")

# --- FUNÇÕES SÍNCRONAS ---

def get_gold(user_id: int) -> int:
    dados = _carregar_dados_raw()
    user_str = str(user_id)
    val = dados.get(user_str, 0)
    
    if isinstance(val, dict):
        return int(val.get("gold", 0))
    if isinstance(val, (int, float)):
        return int(val)
    return 0

def add_gold(user_id: int, valor: int):
    dados = _carregar_dados_raw()
    user_str = str(user_id)
    saldo_atual = get_gold(user_id)
    dados[user_str] = saldo_atual + int(valor)
    _salvar_dados_raw(dados)

def remove_gold(user_id: int, valor: int) -> bool:
    dados = _carregar_dados_raw()
    user_str = str(user_id)
    saldo_atual = get_gold(user_id)
    valor_int = int(valor)
    
    if valor_int <= 0 or saldo_atual < valor_int:
        return False
        
    dados[user_str] = max(0, saldo_atual - valor_int)
    _salvar_dados_raw(dados)
    return True

# --- FUNÇÕES ASSÍNCRONAS (THREAD-SAFE PARA OS BOTÕES/SLASH) ---

async def get_gold_safe(user_id: int) -> int:
    async with _lock:
        return get_gold(user_id)

async def add_gold_safe(user_id: int, valor: int):
    async with _lock:
        add_gold(user_id, valor)

async def remove_gold_safe(user_id: int, valor: int) -> bool:
    async with _lock:
        return remove_gold(user_id, valor)
