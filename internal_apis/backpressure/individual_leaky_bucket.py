from datetime import datetime
from auth_service.controller import AuthenticationController
import redis
import time
from functools import wraps
from flask import Flask, request, jsonify
from auth_service.auth_routes import token_required
import traceback

class LeakyBucket:

    @staticmethod
    def get_redis():
        return redis.Redis.from_url("redis://localhost:6379/0")

    @staticmethod

    def individual_leaky_bucket(bucketcapacity, leakrate, keytimeout):
        def decorator(f):
            @wraps(f)
            def wrapped(*args, **kwargs):
                try:
                    r = LeakyBucket.get_redis()
                    r.ping()
                    print("[DEBUG] Conectado ao Redis com sucesso.")
                except Exception as e:
                    print("[ERRO] Falha ao conectar ao Redis:", e)
                    traceback.print_exc()
                    return jsonify({"status": "erro", "mensagem": "Erro ao conectar ao Redis"}), 500

                client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
                if not client_ip:
                    return jsonify({"message": "Não foi possível identificar o endereço de IP do cliente."}), 400
                key = f"leaky_bucket:{client_ip}"
                print(f"[DEBUG] IP da requisicao: {client_ip}")
                now = time.time()


                try:
                    data = r.hmget(name=key, keys=["last_access", "tokens"])
                    print(f"[DEBUG] Dados brutos do Redis: {data}")
                    last_access = float(data[0]) if data[0] else now
                    tokens = int(data[1]) if data[1] else 0
                    readable_last_access = datetime.fromtimestamp(last_access).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    print(f"[INFO] Último acesso: {readable_last_access}, Tokens agora: {tokens}")
                except Exception as e:
                    print("[ERRO] Falha ao obter ou interpretar dados do Redis:", e)
                    traceback.print_exc()
                    return jsonify({"status": "erro", "mensagem": "Erro ao acessar dados do Redis"}), 500

                time_elapsed = now - last_access
                leaked_tokens = int(time_elapsed / leakrate)
                tokens = max(0, tokens - leaked_tokens)
                if leaked_tokens < 0:
                    last_access = now

                if tokens < bucketcapacity:
                    tokens += 1
                    try:
                        r.hset(name=key, mapping={"tokens": tokens, "last_access": now})
                        r.expire(key, keytimeout)
                        print(f"[INFO] Requisição aceita. Tokens agora: {tokens}")
                        return f(*args, **kwargs)
                    except Exception as e:
                        print("[ERRO] Falha ao atualizar Redis:", e)
                        traceback.print_exc()
                        return jsonify({"status": "erro", "mensagem": "Erro ao atualizar Redis"}), 500
                else:
                    print("[INFO] Bucket cheio. Requisição bloqueada.")
                    return jsonify({"status": "error", "message": "Request limit exceeded!"}), 429

            return wrapped
        return decorator


