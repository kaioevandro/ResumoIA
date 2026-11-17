#!/usr/bin/env python3
"""
Resumo IA — resume textos, extrai tópicos e tarefas com uma API de IA.

Uso:
    python3 resumo_ia.py --arquivo exemplos/reuniao.txt
    python3 resumo_ia.py --arquivo exemplos/reuniao.txt --estilo curto
    python3 resumo_ia.py --texto "texto longo aqui..." --estilo topicos
    echo "texto..." | python3 resumo_ia.py

Configuração (copie .env.example para .env ou exporte as variáveis):
    OPENAI_API_KEY=...
    OPENAI_BASE_URL=https://api.openai.com/v1   # opcional
    OPENAI_MODEL=gpt-4o-mini                        # opcional
    ANTHROPIC_API_KEY=...                           # alternativa, se preferir Claude

Sem chave, o programa roda em modo demonstração: mostra o que enviaria
para a API e um resumo local simples, sem gastar créditos.
Só usa a biblioteca padrão do Python — nenhuma dependência para instalar.
"""

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path

ESTILOS = {
    "curto": "Resuma em até 5 linhas, em português, mantendo só o essencial.",
    "topicos": "Resuma em tópicos curtos, em português, um por linha, começando com '- '.",
    "tarefas": (
        "Resuma em português e, no final, liste as tarefas / próximos passos "
        "em tópicos começando com '- [ ] '."
    ),
}


def carregar_env(caminho=".env"):
    """Lê um arquivo .env simples (CHAVE=valor), sem sobrescrever o ambiente."""
    p = Path(caminho)
    if not p.exists():
        return
    for linha in p.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def resumo_local(texto, estilo):
    """Resumo de demonstração, sem API: primeiras frases + contagem."""
    frases = [f.strip() for f in texto.replace("\n", " ").split(". ") if f.strip()]
    palavras = len(texto.split())
    if estilo == "topicos":
        topicos = frases[:5]
        return "Resumo local (sem API):\n" + "\n".join(f"- {f}" for f in topicos)
    if estilo == "tarefas":
        return (
            f"Resumo local (sem API): texto com {palavras} palavras.\n"
            f"Primeira ideia: {frases[0] if frases else texto[:120]}"
            "\n- [ ] Revisar o resumo gerado pela IA"
        )
    resumo = ". ".join(frases[:3])
    return f"Resumo local (sem API): {resumo} ({palavras} palavras no original.)"


def chamar_openai(texto, estilo, modelo, base_url, chave):
    """Chama um endpoint compatível com OpenAI Chat Completions."""
    url = base_url.rstrip("/") + "/chat/completions"
    corpo = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": "Você resume textos em português, de forma clara e fiel ao original."},
            {"role": "user", "content": f"{ESTILOS[estilo]}\n\nTexto:\n{texto}"},
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


def chamar_anthropic(texto, estilo, modelo, chave):
    """Chama a API de mensagens da Anthropic (Claude)."""
    url = "https://api.anthropic.com/v1/messages"
    corpo = {
        "model": modelo,
        "max_tokens": 1024,
        "system": "Você resume textos em português, de forma clara e fiel ao original.",
        "messages": [
            {"role": "user", "content": f"{ESTILOS[estilo]}\n\nTexto:\n{texto}"}
        ],
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(corpo).encode("utf-8"),
        headers={
            "x-api-key": chave,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        dados = json.loads(resp.read().decode("utf-8"))
    return "".join(
        bloco.get("text", "") for bloco in dados.get("content", []) if bloco.get("type") == "text"
    ).strip()


def main():
    carregar_env()
    parser = argparse.ArgumentParser(description="Resumo IA — resume textos com uma API de IA.")
    parser.add_argument("--arquivo", help="Arquivo .txt com o texto a resumir")
    parser.add_argument("--texto", help="Texto direto na linha de comando")
    parser.add_argument("--estilo", choices=sorted(ESTILOS), default="curto",
                        help="curto, topicos ou tarefas (padrão: curto)")
    parser.add_argument("--modelo", help="Modelo a usar (padrão: OPENAI_MODEL ou gpt-4o-mini)")
    args = parser.parse_args()

    if args.arquivo:
        texto = Path(args.arquivo).read_text(encoding="utf-8")
    elif args.texto:
        texto = args.texto
    elif not sys.stdin.isatty():
        texto = sys.stdin.read()
    else:
        parser.error("Informe --arquivo, --texto ou envie o texto pelo stdin.")

    texto = texto.strip()
    if not texto:
        print("Texto vazio. Nada para resumir.", file=sys.stderr)
        return 1

    chave_openai = os.environ.get("OPENAI_API_KEY", "").strip()
    chave_anthropic = os.environ.get("ANTHROPIC_API_KEY", "").strip()

    if chave_openai:
        modelo = args.modelo or os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        print(f"Usando API compatível com OpenAI, modelo {modelo}...\n")
        print(chamar_openai(texto, args.estilo, modelo, base_url, chave_openai))
    elif chave_anthropic:
        modelo = args.modelo or os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")
        print(f"Usando Anthropic Claude, modelo {modelo}...\n")
        print(chamar_anthropic(texto, args.estilo, modelo, chave_anthropic))
    else:
        print("Sem chave de API configurada — modo demonstração, sem custo.\n")
        print("Configure OPENAI_API_KEY ou ANTHROPIC_API_KEY no .env para usar a IA real.")
        print(resumo_local(texto, args.estilo))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
