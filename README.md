---
# 📁 Ferramentas de Análise e Mapeamento de Projetos

Este repositório contém dois scripts Python práticos, desenvolvidos para te ajudar a entender melhor a estrutura e o conteúdo de projetos, especialmente útil para documentação, auditoria ou até mesmo para alimentar modelos de linguagem (LLMs) com a "anatomia" de um codebase.

Ambos os scripts **ignoram pastas e arquivos sensíveis/irrelevantes** ao gerar relatórios. As regras ficam centralizadas em `exclude_patterns.py` para você ajustar em um único lugar.

---

## 🚀 Scripts Disponíveis

### 📄 `scan_folder.py`
Este script escaneia uma pasta e suas subpastas, extraindo o **conteúdo de arquivos de texto** específicos. Ele é inteligente o suficiente para **ignorar arquivos binários** (como ZIPs ou imagens) e, o mais importante, **divide o relatório final em várias partes**, caso ele fique muito grande (o limite padrão é 100MB por parte). Arquivos e diretórios listados em `exclude_patterns.py` **não entram** no relatório (nem caminho nem conteúdo), com uma exceção de segurança: arquivos `.env` e `.env.*` entram somente em modo **higienizado** (apenas chaves, sem valores).

### 🌳 `map_project.py`
Já este script gera um **mapa detalhado da estrutura de diretórios** do seu projeto. Ele lista todas as pastas e, dentro delas, cada arquivo, mostrando apenas seu nome e tipo (ex: "Código-Fonte", "Configuração"). Ele **não extrai o conteúdo dos arquivos**, focando puramente na organização do projeto. As **mesmas regras de exclusão** de `exclude_patterns.py` se aplicam aqui, mas com uma exceção: arquivos `.env` e `.env.*` são exibidos na árvore por nome.

### 📎 `exclude_patterns.py`
Módulo compartilhado — não é executado diretamente. Define o que os dois scripts **deixam de visitar ou listar**. Ajuste este arquivo se o seu projeto usar outras pastas de ferramentas ou nomes de credenciais.

Regras padrão atuais:
- **Pastas nunca lidas**: `.git`, `.idea`, `.vscode`, `.github`, `node_modules`, `vendor`, `venv`, `.venv`, `dist`, `build`, `out`, `.turbo`, `.next`, `coverage`, `bin`, `pkg`, `__pycache__`, `.pytest_cache`, `.eslintcache`.
- **Extensões nunca lidas/listadas**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.svg`, `.ico`, `.mp4`, `.mp3`, `.zip`, `.tar`, `.gz`, `.exe`, `.dll`, `.so`, `.pyc`, `.log`, `.sqlite`, `.sqlite3`.
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

```bash
python3 scan_folder.py /caminho/para/a/pasta/do/seu/projeto
```

**Exemplo prático:**
```bash
python3 scan_folder.py /home/usuario/meu_app_backend
# Se o caminho tiver espaços, coloque entre aspas:
python3 scan_folder.py "/home/usuario/pasta com espaço no nome"
```
Você verá o progresso no terminal e, ao final, os arquivos de relatório serão gerados em uma pasta dedicada dentro de `relatorios/`, com nomes como `conteudo_parte1_meu_app_backend.txt`, `conteudo_parte2_meu_app_backend.txt`, etc.

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
    ├── conteudo_parte1_meu_app_backend.txt
    └── conteudo_parte2_meu_app_backend.txt
```

Isso permite rodar os scripts várias vezes, em projetos diferentes, sem sobrescrever relatórios antigos.

---

## ⚙️ Quer Personalizar? (Opcional)

Você pode ajustar o comportamento dos scripts editando diretamente os arquivos `.py` em qualquer editor de texto. Procure pelas seções de **constantes de configuração** no início de cada script para modificar:

### Em `exclude_patterns.py`:
* `EXCLUDED_DIR_NAMES`: pastas omitidas dos relatórios (Git/IDE, dependências, build e caches).
* `EXCLUDED_FILE_NAMES`: arquivos omitidos por nome (ex.: lockfiles grandes e credenciais).
* `IGNORED_EXTENSIONS`: extensões irrelevantes que nunca devem ser lidas/listadas (mídia, binários, logs e sqlite).
* `is_env_file()`: identifica `.env` e variantes `.env.*`.
* `should_exclude_file(..., include_env_files=True)`: permite liberar `.env` por contexto de uso.
* `SENSITIVE_EXTENSIONS`: extensões e regras extras para segredos/certificados.

### Em `scan_folder.py`:
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

