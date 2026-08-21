import json
import os
import asyncio

CAMINHO_BANCO = "database_golds.json"

# Trava de segurança para impedir acessos simultâneos ao mesmo arquivo
_lock = asyncio.Lock()

def _carregar_dados_raw() -> dict:
    if not os.path.exists(CAMINHO_BANCO):
        with open(CAMINHO_BANCO, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
    try:
        with open(CAMINHO_BANCO, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao ler {CAMINHO_BANCO}: {e}")
        return {}

def _salvar_dados_raw(dados: dict):
    try:
        with open(CAMINHO_BANCO, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao salvar {CAMINHO_BANCO}: {e}")

# --- FUNÇÕES SÍNCRONAS (COMPATIBILIDADE) ---
def get_gold(user_id: int) -> int:
    dados = _carregar_dados_raw()
    return dados.get(str(user_id), 0)

def add_gold(user_id: int, valor: int):
    dados = _carregar_dados_raw()
    user_str = str(user_id)
    saldo_atual = dados.get(user_str, 0)
    dados[user_str] = saldo_atual + valor
    _salvar_dados_raw(dados)

def remove_gold(user_id: int, valor: int) -> bool:
    dados = _carregar_dados_raw()
    user_str = str(user_id)
    saldo_atual = dados.get(user_str, 0)
    
    if saldo_atual < valor:
        return False
        
    dados[user_str] = max(0, saldo_atual - valor)
    _salvar_dados_raw(dados)
    return True

# --- FUNÇÕES ASSÍNCRONAS COM LOCK (SEGURA CONTRA CORRUPÇÃO) ---
async def get_gold_safe(user_id: int) -> int:
    async with _lock:
        return get_gold(user_id)

async def add_gold_safe(user_id: int, valor: int):
    async with _lock:
        add_gold(user_id, valor)

async def remove_gold_safe(user_id: int, valor: int) -> bool:
    async with _lock:
        return remove_gold(user_id, valor)
