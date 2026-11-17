"""Função serverless da Vercel para o Resumo IA (POST /api/resumir).

A Vercel executa este arquivo como função Python. Sem chave de API
configurada nas variáveis de ambiente, responde com o resumo local de
demonstração, sem custo — o mesmo comportamento do app.py local.
Só usa a biblioteca padrão do Python.
"""

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

ESTILOS = ("curto", "topicos", "tarefas")


def resumo_local(texto, estilo):
    frases = [f.strip() for f in texto.replace("\n", " ").split(". ") if f.strip()]
    palavras = len(texto.split())
    if estilo == "topicos":
        return "Resumo local (sem API):\n" + "\n".join(f"- {f}" for f in frases[:5])
    if estilo == "tarefas":
        return (
            f"Resumo local (sem API): texto com {palavras} palavras.\n"
            f"Primeira ideia: {frases[0] if frases else texto[:120]}"
            "\n- [ ] Revisar o resumo gerado pela IA"
        )
    resumo = ". ".join(frases[:3])
    return f"Resumo local (sem API): {resumo} ({palavras} palavras no original.)"


def chamar_openai(texto, estilo, modelo, base_url, chave):
    url = base_url.rstrip("/") + "/chat/completions"
    corpo = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": "Você resume textos em português, de forma clara e fiel ao original."},
            {"role": "user", "content": f"Resuma em português, estilo {estilo}.\n\nTexto:\n{texto}"},
        ],
        "temperature": 0.3,
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Authorization": f"Bearer {chave}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        dados = json.loads(resp.read().decode("utf-8"))
    return dados["choices"][0]["message"]["content"].strip()


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        tamanho = int(self.headers.get("Content-Length", 0))
        corpo = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        texto = (corpo.get("texto") or "").strip()
        estilo = corpo.get("estilo") or "curto"
        if not texto:
            self._json({"erro": "Envie um texto para resumir."}, 400)
            return
        if estilo not in ESTILOS:
            estilo = "curto"
        chave_openai = os.environ.get("OPENAI_API_KEY", "").strip()
        try:
            if chave_openai:
                modelo = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
                base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
                resultado = chamar_openai(texto, estilo, modelo, base_url, chave_openai)
                provedor = f"OpenAI ({modelo})"
            else:
                resultado = resumo_local(texto, estilo)
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

    def log_message(self, *args):
        pass
