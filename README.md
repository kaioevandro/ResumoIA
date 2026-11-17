# Resumo IA

Ferramenta simples para resumir textos longos, extrair tópicos e listar tarefas — com uma API de IA.

Feita para quem lida com atas, artigos, aulas e documentos e precisa do essencial em poucos segundos. Funciona por linha de comando e pela interface web.

> **Resumo IA** — Summarize long texts, extract topics and tasks with an AI API. CLI + minimal web UI, Python standard library only.

## O que faz

- Resumo curto (até 5 linhas)
- Resumo em tópicos
- Resumo + lista de tarefas / próximos passos
- Interface web em `http://localhost:8000`
- Modo demonstração sem chave: mostra o que seria enviado e gera um resumo local, sem custo

## Como usar

Pré-requisito: Python 3.10 ou superior. Nenhuma dependência para instalar.

```bash
# 1. Configurar a chave (opcional — sem ela, roda em demonstração)
cp .env.example .env
# edite o .env e coloque OPENAI_API_KEY ou ANTHROPIC_API_KEY

# 2. Linha de comando
python3 resumo_ia.py --arquivo exemplos/reuniao.txt
python3 resumo_ia.py --arquivo exemplos/reuniao.txt --estilo topicos
python3 resumo_ia.py --arquivo exemplos/reuniao.txt --estilo tarefas

# 3. Interface web
python3 app.py
# abra http://localhost:8000
```

## Configuração

| Variável | Padrão | Descrição |
|---|---|---|
| `OPENAI_API_KEY` | — | Chave da OpenAI (ou de API compatível) |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Endpoint compatível com OpenAI |
| `OPENAI_MODEL` | `gpt-4o-mini` | Modelo leve e barato para resumos |
| `ANTHROPIC_API_KEY` | — | Alternativa: chave da Anthropic (Claude) |
| `ANTHROPIC_MODEL` | `claude-haiku-4-5` | Modelo leve da Anthropic |

Nunca publique o arquivo `.env`. Ele já está no `.gitignore`.

## Por que usa créditos de API

Cada resumo é uma chamada à API, com o texto de entrada e um resumo curto de saída. Usando um modelo leve, o custo por resumo é baixo e previsível, o que torna o projeto adequado para testar créditos de API em uso real: dá para medir resumos por dia, tokens por resumo e custo médio mensal.

Próximos passos: suporte a arquivos maiores, histórico de resumos e deploy da interface web.

## Licença

MIT — veja `LICENSE`.
