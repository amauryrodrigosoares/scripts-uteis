---
# 📁 Ferramentas de Análise e Mapeamento de Projetos

Este repositório contém dois scripts Python práticos, desenvolvidos para te ajudar a entender melhor a estrutura e o conteúdo de projetos, especialmente útil para documentação, auditoria ou até mesmo para alimentar modelos de linguagem (LLMs) com a "anatomia" de um codebase.

Ambos os scripts **ignoram pastas e arquivos sensíveis/irrelevantes** ao gerar relatórios. As regras ficam centralizadas em `exclude_patterns.py` para você ajustar em um único lugar.

**Notebook LM:** para **melhores resultados**, use primeiro o **`map_project.py`** (árvore `estrutura_notebook_lm.md`) e só depois o **`scan_folder.py`** em modo LM: carregue **`conteudo_projeto_*.md`** (resto do código) e **`conteudo_php_*.md`** (só `.php`/`.phtml`) como fontes **separadas**. Esse modo é usado **automaticamente** se o escaneamento incluir **`.php` ou `.phtml`**, ou sempre que passar **`--php`**. Sem LM, o relatório legacy usa **`conteudo_projeto_*.txt`** e **`conteudo_php_*.txt`** com a mesma separação. Para **forçar** só `.txt` legacy mesmo com PHP no projeto, use **`--legacy-only`**. O detalhe desta ordem repete-se abaixo em «Como usar».

---

## 🚀 Scripts Disponíveis

### 📄 `scan_folder.py`
Este script extrai o **conteúdo de arquivos de texto** (e resumos de binários conhecidos) para um relatório em partes. **Por padrão só olha a raiz** da pasta que você passou: não desce em subpastas. Para varrer o projeto inteiro, use **`-r`**, **`-recursive`** ou **`--recursive`** (equivalentes). Arquivos filtrados por `exclude_patterns.py` não entram no relatório de conteúdo.

**Modo legacy (`.txt`, 100 MB por parte):** usado quando **não** há ficheiros `.php`/`.phtml` no escopo **ou** com **`--legacy-only`**. Há **duas séries** de ficheiros: **`conteudo_projeto_*.txt`** (tudo o que **não** é `.php`/`.phtml`) e **`conteudo_php_*.txt`** (só `.php`/`.phtml`), para manter PHP separado do resto. Delimitadores `--- Caminho do arquivo ---`, espírito `f9b0bf7`. `.env` no fluxo `projeto`.

**Modo Notebook LM (`.md` ou `.xml`, 5 MB por parte):** activado **automaticamente** se existir `.php`/`.phtml` no escopo, ou com **`--php`**. Duas séries: **`conteudo_projeto_*`** (JS, Go, `.html` com PHP embutido, `.env`, etc.) e **`conteudo_php_*`** (apenas extensões `.php`/`.phtml`). Cabeçalho `# Arquivo:` (MD), preâmbulo por série. Nos blocos com **PHP para NLM** (ficheiro `.php`/`.phtml` ou PHP embutido no conteúdo), **formato plano** com omissão/máscara; **outras** linguagens com cercas `` ```lang ``. Use **`--raw-php`** / **`--nl-plain`** como antes. Os ficheiros no disco **nunca** são alterados.

### 🌳 `map_project.py`
Já este script gera um **mapa detalhado da estrutura de diretórios** do seu projeto (**sempre recursivo** em toda a árvore). Ele lista pastas e arquivos **pelo nome** (a extensão já identifica o tipo), **sem** extrair conteúdo. **Imagens, vídeos, zips e outras extensões “pesadas” entram na árvore** (para contexto). Continuam valendo exclusões de segurança (credenciais, lockfiles, `.pem`, etc.) e `.env` / `.env.*` aparecem por nome.

### 📎 `exclude_patterns.py`
Módulo compartilhado — não é executado diretamente. Define o que os dois scripts **deixam de visitar ou listar**. Ajuste este arquivo se o seu projeto usar outras pastas de ferramentas ou nomes de credenciais.

Regras padrão atuais:
- **Pastas nunca lidas**: `.git`, `.idea`, `.vscode`, `.github`, `node_modules`, `vendor`, `venv`, `.venv`, `dist`, `build`, `out`, `.turbo`, `.next`, `coverage`, `bin`, `pkg`, `__pycache__`, `.pytest_cache`, `.eslintcache`.
- **Extensões ignoradas só no relatório de conteúdo** (`scan_folder.py`): imagens, áudio/vídeo, compactados, binários comuns, `.log`, `.sql`, `.sqlite`, etc. — lista em `IGNORED_EXTENSIONS`. No **mapa de estrutura** (`map_project.py`) esses arquivos **continuam listados** (só o nome), para você ver que existem no projeto.
- **Arquivos específicos ignorados**: `package-lock.json`, `yarn.lock`, `composer.lock`, `go.sum` (além dos já sensíveis como `.npmrc`, chaves e certificados).
- **Regra especial para `.env`**: quando habilitado no contexto do script, `.env` e `.env.*` são processados com mascaramento de valores.

---

## 📂 Arquivos neste repositório

| Arquivo | Função |
|--------|--------|
| `scan_folder.py` | Duas séries: **`conteudo_projeto_*`** (não PHP) e **`conteudo_php_*`** (`.php`/`.phtml`). **`.txt`** legacy ou **`.md`/`.xml`** no LM (auto com PHP no escopo ou **`--php`**); **`--legacy-only`** força `.txt` |
| `map_project.py` | Gera `estrutura_notebook_lm.md` (árvore mínima `D`/`F` para Notebook LM) |
| `exclude_patterns.py` | Listas e funções de exclusão (IDE, Git, build, lockfiles, mídia e segredos) |
| `scan_folder_content.py` | Legado: redireciona para `scan_folder.py` |
| `map_project_structure.py` | Legado: redireciona para `map_project.py` |

Os arquivos `.py` usados na execução devem ficar **na mesma pasta** que `exclude_patterns.py` para o `import` funcionar.

---

## ✨ Como Eles Podem te Ajudar

### Para `scan_folder.py`:
* **Notebook LM:** depois do mapa (`map_project.py`), execute **`scan_folder.py`** e carregue **`conteudo_projeto_*.md`** e **`conteudo_php_*.md`** como fontes distintas — ver **«Notebook LM: ordem recomendada»**. Com **`--php`** força-se o modo LM mesmo sem `.php` na raiz. Com **`--legacy-only`**, saída **`.txt`** com o mesmo par de séries (`conteudo_projeto_*` / `conteudo_php_*`).
* **Foco no Conteúdo Relevante**: Extrai apenas o que importa (código, logs, configurações), ignorando lixo.
* **Relatórios Gerenciáveis**: O relatório é dividido em partes (100 MB no legacy; 5 MB com `--php`).
* **Com `--php` (Markdown):** cada ficheiro usa `# Arquivo:` (caminho absoluto). **PHP** (extensão `.php`/`.phtml` ou PHP embutido detetado) em formato plano (NLM); **outras linguagens** com cercas `` ```lang ``.
* **Notebook LM (só com `--php`)**: Cada parte `.md` explica o **formato misto**. Nos blocos PHP para NLM: `<?php` **omitido**; `__NLM_PHP_ECHO_OPEN__` e `__NLM_PHP_SHORT_OPEN__` substituem `<?=` e short `<?`+espaço. **`--raw-php`**: PHP de volta a cercas literais. **`--nl-plain`**: força formato plano **em todas** as linguagens (só se o NLM também cortar Go/JS/etc.).
* **Nomenclatura Inteligente**: Os relatórios são nomeados automaticamente com o caminho do projeto e um timestamp, para que você nunca se perca.

### Para `map_project.py`:
* **Visão Geral Rápida**: Tenha um entendimento instantâneo da hierarquia do projeto.
* **Notebook LM / tokens**: Gera um único `estrutura_notebook_lm.md` — o arquivo é Markdown só no sentido da extensão; o conteúdo é texto puro (sem títulos, YAML nem cercas), uma linha por pasta (`D caminho/`) ou arquivo (`F caminho`), caminhos em POSIX. Caracteres que costumam quebrar ingestão (quebras de linha, crase, controle) são normalizados nos caminhos.
* **Notebook LM:** carregue **esta fonte primeiro** (antes de `conteudo_projeto_*.md` e `conteudo_php_*.md`) para o modelo ter a árvore antes de ler o código.

---

## 🛠️ Começando Rápido

### Pré-requisitos
Você só precisa ter o **Python 3** instalado no seu sistema Linux. Nada mais! Nos exemplos abaixo, use `python3` no terminal se o comando `python` não apontar para a versão 3.

### Instalação
Não tem instalação! É só baixar os arquivos:
1.  **Baixe os arquivos**: Salve `scan_folder.py`, `map_project.py` e `exclude_patterns.py` na mesma pasta (opcional: mantenha os wrappers legados se precisar de compatibilidade).

### Como Usar

O jeito mais simples é ir até a pasta onde estão os scripts e executar os comandos abaixo. Também funciona chamar pelo **caminho absoluto** (por exemplo `python3 /opt/scripts-uteis/scan_folder.py /meu/projeto`), desde que `exclude_patterns.py` continue na mesma pasta que o script que você executa.

### Notebook LM: ordem recomendada (melhores resultados)

1. **Executar `map_project.py` primeiro** na pasta do projeto e **carregar** o `estrutura_notebook_lm.md` no Notebook LM. Assim o modelo recebe a **árvore** (`D` / `F`) com todos os caminhos e nomes de ficheiros, de forma compacta.
2. **Executar `scan_folder.py`** a seguir (normalmente com **`-r`**; com `.php`/`.phtml` no escopo o modo LM é automático; senão **`--php`**) e **carregar** `conteudo_projeto_*.md` e `conteudo_php_*.md` como fontes adicionais.

Com **estrutura antes do conteúdo**, o LM costuma **situar-se melhor** no repositório, ligar perguntas do tipo «onde está X?» aos ficheiros certos e usar o código com menos erros de contexto. Se inverter a ordem ou só subir o dump de conteúdo, ainda funciona, mas a experiência tende a ser pior.

#### 1. Para escanear o conteúdo do projeto (`scan_folder.py`)

Por padrão, **só a raiz** da pasta (arquivos diretos, sem subpastas). A saída é em **duas séries** (`conteudo_projeto_*` + `conteudo_php_*`), em **`.txt`** (legacy, 100 MB por parte) **exceto** se existir **`.php` ou `.phtml`** no escopo — aí passa a **`.md`** (modo LM, 5 MB por parte) **sem precisar de `--php`**.

```bash
python3 scan_folder.py /caminho/para/a/pasta/do/seu/projeto
```

Para incluir **todas as subpastas** (projeto inteiro):

```bash
python3 scan_folder.py --recursive /caminho/para/a/pasta/do/seu/projeto
# ou (equivalente)
python3 scan_folder.py /caminho/para/a/pasta/do/seu/projeto -r
python3 scan_folder.py /caminho/para/a/pasta/do/seu/projeto -recursive
```

**Forçar modo Notebook LM** (útil em projectos só JS na raiz mas PHP noutras pastas: use **`-r`** ou **`--php`**):

```bash
python3 scan_folder.py --php -r /caminho/para/o/projeto
# Sempre .txt mesmo com .php na pasta:
python3 scan_folder.py --legacy-only -r /caminho/para/o/projeto
# PHP literal nas cercas (sem máscara NLM no Markdown):
python3 scan_folder.py --raw-php -r /home/usuario/meu_app_backend
# Saída XML em vez de Markdown (requer modo LM: --php ou .php no escopo):
python3 scan_folder.py -xml -r /home/usuario/meu_app_backend
# Formato plano em todas as linguagens (só se o NLM cortar também Go/JS/etc.):
python3 scan_folder.py --nl-plain -r /home/usuario/meu_app_backend
```

**Exemplo prático:**
```bash
python3 scan_folder.py /home/usuario/meu_app_backend
python3 scan_folder.py -r /home/usuario/meu_app_backend
# Se o caminho tiver espaços, coloque entre aspas:
python3 scan_folder.py "/home/usuario/pasta com espaço no nome"
# Forçar .md quando a raiz não tem .php mas quer o formato LM:
python3 scan_folder.py --php -r /home/usuario/meu_app_backend
```

Você verá o progresso no terminal e, ao final, os relatórios em `relatorios/…/` com **`conteudo_projeto_*`** e **`conteudo_php_*`** (extensão `.txt` ou `.md` / `.xml` conforme o modo). Com **`-xml`** no modo LM, ambas as séries usam `.xml`.

---

## Notebook LM: só aparecem títulos e não há código?

**Modo LM:** existem **`conteudo_projeto_*.md`** e **`conteudo_php_*.md`** quando o escaneamento inclui **`.php`/`.phtml`** (automático) ou com **`--php`**. Caso contrário ou com **`--legacy-only`**, as mesmas séries em **`.txt`** com `--- Caminho do arquivo ---`.

**Diagnóstico rápido (cerca de 1 minuto):** abra **`conteudo_projeto_*.md`** e **`conteudo_php_*.md`** no disco. Procure `# Arquivo:` e o corpo (cercas ou bloco plano).

- Se existir um bloco entre `` ``` `` … `` ``` `` **com linhas de código**, ou entre `---------- inicio-corpo ----------` e `---------- fim-corpo ----------` **com linhas começadas por `| `**, o `scan_folder.py` em modo LM **gravou o conteúdo**. Se no Notebook LM só vê títulos, o problema é **ingestão ou visualização no LM** (resumo do chat, sanitização, etc.), não “o script não leu os ficheiros”.
- Se **no disco** também não houver corpo entre dois `# Arquivo:`, aí sim vale rever o comando (por exemplo **`-r`** se o PHP está em subpastas — o auto-LM só conta ficheiros no **mesmo** escopo do escaneamento) ou exclusões em `exclude_patterns.py`.

**O que experimentar no LM:** carregue **`estrutura_notebook_lm.md` primeiro**, depois **`conteudo_projeto_*.md`** e **`conteudo_php_*.md`** (ver **«Notebook LM: ordem recomendada»**). Ficheiros **`.php`/`.phtml`** vão só em `conteudo_php_*`; **PHP embutido** em `.html` etc. fica em `conteudo_projeto_*` com formato plano NLM nesse bloco. Se **todas** as linguagens forem cortadas pelo NLM, use **`--nl-plain`**.

---

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
O script vai informar onde o relatório de estrutura será salvo. O arquivo gerado terá o nome fixo `estrutura_notebook_lm.md` dentro da pasta da execução.

---

## 📦 Onde os arquivos são salvos?

Para manter seu ambiente organizado, os scripts **não jogam arquivos soltos** na raiz do projeto.

Sempre que você executa qualquer um dos scripts, ele cria automaticamente uma pasta `relatorios/` (no mesmo diretório onde os scripts estão). Dentro dela, é criada uma subpasta exclusiva para aquela execução, com nome do projeto e data/hora.

Exemplo de saída:

```text
relatorios/
└── relatorio_meu_app_backend_20250610_124500/
    ├── estrutura_notebook_lm.md
    └── conteudo_projeto_meu_app_backend.txt
    # (+ conteudo_php_*.txt na mesma pasta se o escopo incluir .php/.phtml)
```

Em modo LM (`.md` ou `.xml`), os nomes são **`conteudo_projeto_*`** e **`conteudo_php_*`** com a extensão respectiva.

(Fatiamento: `conteudo_projeto_2_…`, `conteudo_php_2_…`, etc., conforme o limite de tamanho por parte.)

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
* Linha de comando: `python3 scan_folder.py <pasta>` (só raiz) ou recursivo com `-r` / `-recursive` / `--recursive`. Duas séries de ficheiros: **`conteudo_projeto_*`** (não `.php`/`.phtml`) e **`conteudo_php_*`** (só essas extensões). **`.txt`** (legacy) se não houver `.php`/`.phtml` no escopo ou com **`--legacy-only`**; **`.md`/`.xml`** (LM) se houver PHP no escopo **ou** com **`--php`**. **Notebook LM:** preâmbulo por série; PHP para NLM em plano onde aplicável; **`--raw-php`**; **`--nl-plain`**.
* Constantes de token NLM (apenas export MD com `--php`): `NLM_PHP_ECHO_TOKEN`, `NLM_PHP_SHORT_TOKEN` — ajuste se quiser outros marcadores; `<?php` não usa token (é removido do texto exportado).
* `LEGACY_MAX_REPORT_FILE_SIZE_BYTES`: tamanho máximo por parte no modo **legacy** (`.txt` / `--legacy-only`, padrão: 100 MB).
* `MAX_REPORT_FILE_SIZE_BYTES`: tamanho máximo por parte no modo **Notebook LM** (padrão: 5 MB).
* `_folder_has_scannable_php_files()`: decide se há `.php`/`.phtml` no escopo para **activar** o modo LM sem `--php`.
* `TEXT_EXTENSIONS`: As extensões de arquivos que o script deve tentar ler o conteúdo.
* `TEXT_FILENAMES_NO_EXT`: Nomes de arquivos específicos que o script deve ler o conteúdo.
* `BINARY_EXTENSIONS`: Extensões de arquivos que o script **nunca** deve tentar ler o conteúdo (são binários).
* `.env` / `.env.*`: no **legacy**, bloco `higienizar_env` com delimitadores antigos; com **`--php`**, leitura higienizada e cerca `` ```dotenv `` no Markdown.

### Em `map_project.py`:
* Saída mínima em `estrutura_notebook_lm.md` (formato `D`/`F`); ajuste `_safe_tree_path` se precisar de outra regra de sanitização de nomes.

---

## Privacidade e limitações

As exclusões **reduzem** o risco de vazar segredos ou lixo de IDE/Git nos relatórios, mas não substituem uma revisão manual nem ferramentas de detecção de credenciais. Arquivos com **nomes fora da lista** (por exemplo um `secrets.json` customizado) ainda podem ser incluídos: nesse caso, acrescente o padrão em `exclude_patterns.py` ou não compartilhe o relatório gerado.

Arquivos `.env` e `.env.*` podem aparecer no relatório de conteúdo, mas sempre com os valores mascarados como `[OCULTADO_POR_SEGURANCA]`. O relatório de estrutura mostra apenas os nomes desses arquivos na árvore.

