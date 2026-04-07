---
# 📁 Ferramentas de Análise e Mapeamento de Projetos

Este repositório contém dois scripts Python práticos, desenvolvidos para te ajudar a entender melhor a estrutura e o conteúdo de projetos, especialmente útil para documentação, auditoria ou até mesmo para alimentar modelos de linguagem (LLMs) com a "anatomia" de um codebase.

Ambos os scripts **ignoram pastas e arquivos sensíveis/irrelevantes** ao gerar relatórios. As regras ficam centralizadas em `exclude_patterns.py` para você ajustar em um único lugar.

---

## 🚀 Scripts Disponíveis

### 📄 `scan_folder.py`
Este script extrai o **conteúdo de arquivos de texto** (e resumos de binários conhecidos) para um relatório em partes (limite padrão **100 MB** por parte). **Por padrão só olha a raiz** da pasta que você passou: não desce em subpastas. Para varrer o projeto inteiro, use **`-r`**, **`-recursive`** ou **`--recursive`** (equivalentes). Arquivos filtrados por `exclude_patterns.py` não entram no relatório de conteúdo; `.env` / `.env.*` entram só **higienizados** (só chaves). Em **`.php`** e **`.phtml`**, o literal de abertura `<?php` é **removido só no texto do relatório** (case-insensitive), para evitar que consumidores tipo XML/notebook quebrem; os arquivos no disco não são alterados.

### 🌳 `map_project.py`
Já este script gera um **mapa detalhado da estrutura de diretórios** do seu projeto (**sempre recursivo** em toda a árvore). Ele lista pastas e arquivos com nome e tipo (ex.: "Código-Fonte", "Configuração"), **sem** extrair conteúdo. **Imagens, vídeos, zips e outras extensões “pesadas” entram na árvore** (para contexto). Continuam valendo exclusões de segurança (credenciais, lockfiles, `.pem`, etc.) e `.env` / `.env.*` aparecem por nome.

### 📎 `exclude_patterns.py`
Módulo compartilhado — não é executado diretamente. Define o que os dois scripts **deixam de visitar ou listar**. Ajuste este arquivo se o seu projeto usar outras pastas de ferramentas ou nomes de credenciais.

Regras padrão atuais:
- **Pastas nunca lidas**: `.git`, `.idea`, `.vscode`, `.github`, `node_modules`, `vendor`, `venv`, `.venv`, `dist`, `build`, `out`, `.turbo`, `.next`, `coverage`, `bin`, `pkg`, `__pycache__`, `.pytest_cache`, `.eslintcache`.
- **Extensões ignoradas só no relatório de conteúdo** (`scan_folder.py`): imagens, áudio/vídeo, compactados, binários comuns, `.log`, `.sql`, `.sqlite`, etc. — lista em `IGNORED_EXTENSIONS`. No **mapa de estrutura** (`map_project.py`) esses arquivos **continuam listados** (só o nome/tipo), para você ver que existem no projeto.
- **Arquivos específicos ignorados**: `package-lock.json`, `yarn.lock`, `composer.lock`, `go.sum` (além dos já sensíveis como `.npmrc`, chaves e certificados).
- **Regra especial para `.env`**: quando habilitado no contexto do script, `.env` e `.env.*` são processados com mascaramento de valores.

---

## 📂 Arquivos neste repositório

| Arquivo | Função |
|--------|--------|
| `scan_folder.py` | Lê texto de arquivos permitidos e gera relatório(ies) em partes |
| `map_project.py` | Gera árvore de diretórios com tipos de arquivo |
| `exclude_patterns.py` | Listas e funções de exclusão (IDE, Git, build, lockfiles, mídia e segredos) |
| `scan_folder_content.py` | Legado: redireciona para `scan_folder.py` |
| `map_project_structure.py` | Legado: redireciona para `map_project.py` |

Os arquivos `.py` usados na execução devem ficar **na mesma pasta** que `exclude_patterns.py` para o `import` funcionar.

---

## ✨ Como Eles Podem te Ajudar

### Para `scan_folder.py`:
* **Foco no Conteúdo Relevante**: Extrai apenas o que importa (código, logs, configurações), ignorando lixo.
* **Relatórios Gerenciáveis**: Chega de arquivos gigantes que travam seu editor! O relatório é dividido em partes menores e mais fáceis de abrir e analisar.
* **Identificação Clara**: Delimitadores visuais no relatório facilitam a navegação entre o conteúdo de diferentes arquivos.
* **Nomenclatura Inteligente**: Os relatórios são nomeados automaticamente com o caminho do projeto e um timestamp, para que você nunca se perca.

### Para `map_project.py`:
* **Visão Geral Rápida**: Tenha um entendimento instantâneo da hierarquia do projeto.
* **Organização para LLMs**: Ótimo para modelos de linguagem que precisam "compreender" a estrutura de um repositório antes de analisar o código.
* **Formato Amigável**: A formatação em árvore com indentação e símbolos (`[D]` para diretório, `[F]` para arquivo) é super fácil de ler.

---

## 🛠️ Começando Rápido

### Pré-requisitos
Você só precisa ter o **Python 3** instalado no seu sistema Linux. Nada mais! Nos exemplos abaixo, use `python3` no terminal se o comando `python` não apontar para a versão 3.

### Instalação
Não tem instalação! É só baixar os arquivos:
1.  **Baixe os arquivos**: Salve `scan_folder.py`, `map_project.py` e `exclude_patterns.py` na mesma pasta (opcional: mantenha os wrappers legados se precisar de compatibilidade).

### Como Usar

O jeito mais simples é ir até a pasta onde estão os scripts e executar os comandos abaixo. Também funciona chamar pelo **caminho absoluto** (por exemplo `python3 /opt/scripts-uteis/scan_folder.py /meu/projeto`), desde que `exclude_patterns.py` continue na mesma pasta que o script que você executa.

#### 1. Para escanear o conteúdo do projeto (`scan_folder.py`)

Por padrão, **só a raiz** da pasta (arquivos diretos, sem subpastas):

```bash
python3 scan_folder.py /caminho/para/a/pasta/do/seu/projeto
```

Para incluir **todas as subpastas** (comportamento antigo / projeto inteiro):

```bash
python3 scan_folder.py --recursive /caminho/para/a/pasta/do/seu/projeto
# ou (equivalente)
python3 scan_folder.py /caminho/para/a/pasta/do/seu/projeto -r
python3 scan_folder.py /caminho/para/a/pasta/do/seu/projeto -recursive
```

**Exemplo prático:**
```bash
python3 scan_folder.py /home/usuario/meu_app_backend
python3 scan_folder.py -r /home/usuario/meu_app_backend
# Se o caminho tiver espaços, coloque entre aspas:
python3 scan_folder.py "/home/usuario/pasta com espaço no nome"
```
Você verá o progresso no terminal e, ao final, os arquivos de relatório serão gerados em uma pasta dedicada dentro de `relatorios/`. Se couber tudo em um único arquivo (até o limite por parte), o nome é `conteudo_meu_app_backend.txt`. Se houver mais de uma parte, os arquivos passam a ser `conteudo_1_meu_app_backend.txt`, `conteudo_2_meu_app_backend.txt`, etc.

#### 2. Para mapear a estrutura do projeto (`map_project.py`)

```bash
python3 map_project.py /caminho/para/a/pasta/do/seu/projeto
```

**Exemplo prático:**
```bash
python3 map_project.py /home/usuario/site_institucional
# Se o caminho tiver espaços, coloque entre aspas:
python3 map_project.py "/home/usuario/site institucional"
```
O script vai informar onde o relatório de estrutura será salvo. O arquivo gerado terá o nome fixo `estrutura_do_projeto.txt` dentro da pasta da execução.

---

## 📦 Onde os arquivos são salvos?

Para manter seu ambiente organizado, os scripts **não jogam arquivos soltos** na raiz do projeto.

Sempre que você executa qualquer um dos scripts, ele cria automaticamente uma pasta `relatorios/` (no mesmo diretório onde os scripts estão). Dentro dela, é criada uma subpasta exclusiva para aquela execução, com nome do projeto e data/hora.

Exemplo de saída:

```text
relatorios/
└── relatorio_meu_app_backend_20250610_124500/
    ├── estrutura_do_projeto.txt
    └── conteudo_meu_app_backend.txt
```

(Se o dump de conteúdo for fatiado em mais de um arquivo, os nomes passam a ser `conteudo_1_...`, `conteudo_2_...`, e assim por diante.)

Isso permite rodar os scripts várias vezes, em projetos diferentes, sem sobrescrever relatórios antigos.

---

## ⚙️ Quer Personalizar? (Opcional)

Você pode ajustar o comportamento dos scripts editando diretamente os arquivos `.py` em qualquer editor de texto. Procure pelas seções de **constantes de configuração** no início de cada script para modificar:

### Em `exclude_patterns.py`:
* `EXCLUDED_DIR_NAMES`: pastas omitidas dos relatórios (Git/IDE, dependências, build e caches).
* `EXCLUDED_FILE_NAMES`: arquivos omitidos por nome (ex.: lockfiles grandes e credenciais).
* `IGNORED_EXTENSIONS`: extensões omitidas **apenas** no dump de conteúdo (`for_content_scan=True`); no mapa de estrutura não se aplicam.
* `is_env_file()`: identifica `.env` e variantes `.env.*`.
* `should_exclude_file(..., include_env_files=True, for_content_scan=...)`: `for_content_scan=True` no `scan_folder`; `False` no `map_project`.
* `SENSITIVE_EXTENSIONS`: extensões e regras extras para segredos/certificados.

### Em `scan_folder.py`:
* Linha de comando: `python3 scan_folder.py <pasta>` (só raiz) ou recursivo com `-r`, `-recursive` ou `--recursive` antes ou depois do caminho.
* `MAX_REPORT_FILE_SIZE_BYTES`: O tamanho máximo (em bytes) de cada parte do relatório de saída (padrão: 100 MB).
* `TEXT_EXTENSIONS`: As extensões de arquivos que o script deve tentar ler o conteúdo.
* `TEXT_FILENAMES_NO_EXT`: Nomes de arquivos específicos que o script deve ler o conteúdo.
* `BINARY_EXTENSIONS`: Extensões de arquivos que o script **nunca** deve tentar ler o conteúdo (são binários).
* `higienizar_env(filepath)`: lê `.env`/`.env.*` e grava apenas `CHAVE=[OCULTADO_POR_SEGURANCA]`.

### Em `map_project.py`:
* As listas `PROGRAMMING_FILES`, `CONFIG_FILES`, `DOCUMENT_FILES`, `IMAGE_FILES`, `ARCHIVE_FILES` — defina como o script categoriza os diferentes tipos de arquivos do seu projeto.

---

## Privacidade e limitações

As exclusões **reduzem** o risco de vazar segredos ou lixo de IDE/Git nos relatórios, mas não substituem uma revisão manual nem ferramentas de detecção de credenciais. Arquivos com **nomes fora da lista** (por exemplo um `secrets.json` customizado) ainda podem ser incluídos: nesse caso, acrescente o padrão em `exclude_patterns.py` ou não compartilhe o relatório gerado.

Arquivos `.env` e `.env.*` podem aparecer no relatório de conteúdo, mas sempre com os valores mascarados como `[OCULTADO_POR_SEGURANCA]`. O relatório de estrutura mostra apenas os nomes desses arquivos na árvore.

