#!/usr/bin/env python3
"""
Servidor web mínimo do Resumo IA (só biblioteca padrão).

    python3 app.py
    # abre http://localhost:8000

A página envia o texto para /api/resumir, que reutiliza resumo_ia.py.
Sem chave de API, responde com o resumo local de demonstração.
"""

import json
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import resumo_ia

PORTA = 8000


class Handler(SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/api/resumir":
            self.send_error(404, "Rota não encontrada")
            return
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        texto = (corpo.get("texto") or "").strip()
        estilo = corpo.get("estilo") or "curto"
        if not texto:
            self._json({"erro": "Envie um texto para resumir."}, 400)
            return
        if estilo not in resumo_ia.ESTILOS:
            estilo = "curto"
        resumo_ia.carregar_env()
        import os

        chave_openai = os.environ.get("OPENAI_API_KEY", "").strip()
        chave_anthropic = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        try:
            if chave_openai:
                modelo = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
                base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
                resultado = resumo_ia.chamar_openai(texto, estilo, modelo, base_url, chave_openai)
                provedor = f"OpenAI ({modelo})"
            elif chave_anthropic:
                modelo = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
                resultado = resumo_ia.chamar_anthropic(texto, estilo, modelo, chave_anthropic)
                provedor = f"Anthropic Claude ({modelo})"
            else:
                resultado = resumo_ia.resumo_local(texto, estilo)
                provedor = "demonstração local (sem API)"
        except Exception as erro:  # noqa: BLE001 - mostrar o erro na interface
            self._json({"erro": f"Falha ao chamar a API: {erro}"}, 502)
            return
        self._json({"resumo": resultado, "provedor": provedor})

    def _json(self, dados, status=200):
        corpo = json.dumps(dados, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *args):  # silencia logs de cada requisição
        pass


if __name__ == "__main__":
    print(f"Resumo IA em http://localhost:{PORTA} — Ctrl+C para parar")
    ThreadingHTTPServer(("127.0.0.1", PORTA), Handler).serve_forever()
