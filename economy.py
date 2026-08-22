import json
import os
import asyncio
import logging

CAMINHO_BANCO = "database_golds.json"

_lock = asyncio.Lock()

# =========================================================
# LEITURA E GRAVAÇÃO DE DADOS
# =========================================================
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

# =========================================================
# FUNÇÕES SÍNCRONAS COM TRATAMENTO DE TIPOS
# =========================================================
def get_gold(user_id: int) -> int:
    dados = _carregar_dados_raw()
    user_str = str(user_id)
    val = dados.get(user_str, 0)
    
    # Suporte para salvar se for int/float ou dict legado Ex: {"gold": 100}
    if isinstance(val, dict):
        return int(val.get("gold", 0))
    if isinstance(val, (int, float)):
        return int(val)
    return 0

def add_gold(user_id: int, valor: int):
    dados = _carregar_dados_raw()
    user_str = str(user_id)
    saldo_atual = get_gold(user_id)
    
    # Mantém a integridade e salva como inteiro puro
    dados[user_str] = saldo_atual + max(0, int(valor))
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

def get_top_richest(limit: int = 10) -> list:
    """
    Retorna a lista do ranking dos mais ricos formatada para o comando /rank do main.py
    Estrutura de retorno: [(user_id, {"gold": saldo}), ...]
    """
    dados = _carregar_dados_raw()
    
    ranking = []
    for user_id_str, val in dados.items():
        if isinstance(val, dict):
            saldo = int(val.get("gold", 0))
        elif isinstance(val, (int, float)):
            saldo = int(val)
        else:
            saldo = 0
            
        if saldo > 0:
            ranking.append((user_id_str, {"gold": saldo}))
            
    # Ordena pelo maior saldo de golds
    ranking.sort(key=lambda x: x[1]["gold"], reverse=True)
    return ranking[:limit]

# =========================================================
# FUNÇÕES ASSÍNCRONAS SEGURAS (THREAD-SAFE)
# =========================================================
async def get_gold_safe(user_id: int) -> int:
    async with _lock:
        return get_gold(user_id)

async def add_gold_safe(user_id: int, valor: int):
    async with _lock:
        add_gold(user_id, valor)

async def remove_gold_safe(user_id: int, valor: int) -> bool:
    async with _lock:
        return remove_gold(user_id, valor)

async def get_top_richest_safe(limit: int = 10) -> list:
    async with _lock:
        return get_top_richest(limit)
