---
# 📁 Ferramentas de Análise e Mapeamento de Projetos

Este repositório contém dois scripts Python práticos, desenvolvidos para te ajudar a entender melhor a estrutura e o conteúdo de projetos, especialmente útil para documentação, auditoria ou até mesmo para alimentar modelos de linguagem (LLMs) com a "anatomia" de um codebase.

---

## 🚀 Scripts Disponíveis

### 📄 `scan_folder_auto_report.py`
Este script escaneia uma pasta e suas subpastas, extraindo o **conteúdo de arquivos de texto** específicos. Ele é inteligente o suficiente para **ignorar arquivos binários** (como ZIPs ou imagens) e, o mais importante, **divide o relatório final em várias partes**, caso ele fique muito grande (o limite padrão é 185MB por parte).

### 🌳 `map_project_structure.py`
Já este script gera um **mapa detalhado da estrutura de diretórios** do seu projeto. Ele lista todas as pastas e, dentro delas, cada arquivo, mostrando apenas seu nome e tipo (ex: "Código-Fonte", "Configuração"). Ele **não extrai o conteúdo dos arquivos**, focando puramente na organização do projeto.

---

## ✨ Como Eles Podem te Ajudar

### Para `scan_folder_auto_report.py`:
* **Foco no Conteúdo Relevante**: Extrai apenas o que importa (código, logs, configurações), ignorando lixo.
* **Relatórios Gerenciáveis**: Chega de arquivos gigantes que travam seu editor! O relatório é dividido em partes menores e mais fáceis de abrir e analisar.
* **Identificação Clara**: Delimitadores visuais no relatório facilitam a navegação entre o conteúdo de diferentes arquivos.
* **Nomenclatura Inteligente**: Os relatórios são nomeados automaticamente com o caminho do projeto e um timestamp, para que você nunca se perca.

### Para `map_project_structure.py`:
* **Visão Geral Rápida**: Tenha um entendimento instantâneo da hierarquia do projeto.
* **Organização para LLMs**: Ótimo para modelos de linguagem que precisam "compreender" a estrutura de um repositório antes de analisar o código.
* **Formato Amigável**: A formatação em árvore com indentação e símbolos (`[D]` para diretório, `[F]` para arquivo) é super fácil de ler.

---

## 🛠️ Começando Rápido

### Pré-requisitos
Você só precisa ter o **Python 3** instalado no seu sistema Linux. Nada mais!

### Instalação
Não tem instalação! É só baixar os arquivos:
1.  **Baixe os scripts**: Salve `scan_folder_auto_report.py` e `map_project_structure.py` em uma pasta de sua escolha.

### Como Usar

Abra seu terminal, vá para a pasta onde você salvou os scripts e chame o Python para executá-los.

#### 1. Para escanear o conteúdo do projeto (`scan_folder_auto_report.py`)

```bash
python scan_folder_auto_report.py /caminho/para/a/pasta/do/seu/projeto
```

**Exemplo prático:**
```bash
python scan_folder_auto_report.py /home/usuario/meu_app_backend
# Se o caminho tiver espaços, coloque entre aspas:
python scan_folder_auto_report.py "/home/usuario/pasta com espaço no nome"
```
Você verá o progresso no terminal e, ao final, os arquivos de relatório serão gerados na mesma pasta onde o script está, com nomes como `scan-report-home-usuario-meu_app_backend-20250610_124500-parte1.txt`, `scan-report-home-usuario-meu_app_backend-20250610_124500-parte2.txt`, etc.

#### 2. Para mapear a estrutura do projeto (`map_project_structure.py`)

```bash
python map_project_structure.py /caminho/para/a/pasta/do/seu/projeto
```

**Exemplo prático:**
```bash
python map_project_structure.py /home/usuario/site_institucional
# Se o caminho tiver espaços, coloque entre aspas:
python map_project_structure.py "/home/usuario/site institucional"
```
O script vai informar onde o relatório de estrutura será salvo. O arquivo gerado terá um nome parecido com `project-structure-map-home-usuario-site_institucional-20250610_124600.txt`, também na mesma pasta do script.

---

## ⚙️ Quer Personalizar? (Opcional)

Você pode ajustar o comportamento dos scripts editando diretamente os arquivos `.py` em qualquer editor de texto. Procure pelas seções de **constantes de configuração** no início de cada script para modificar:

### Em `scan_folder_auto_report.py`:
* `MAX_REPORT_FILE_SIZE_BYTES`: O tamanho máximo (em bytes) de cada parte do relatório de saída (padrão: 185 MB).
* `TEXT_EXTENSIONS`: As extensões de arquivos que o script deve tentar ler o conteúdo.
* `TEXT_FILENAMES_NO_EXT`: Nomes de arquivos específicos (sem extensão, como `.env`) que o script deve ler o conteúdo.
* `BINARY_EXTENSIONS`: Extensões de arquivos que o script **nunca** deve tentar ler o conteúdo (são binários).

### Em `map_project_structure.py`:
* As listas `PROGRAMMING_FILES`, `CONFIG_FILES`, `DOCUMENT_FILES`, `IMAGE_FILES`, `ARCHIVE_FILES` — defina como o script categoriza os diferentes tipos de arquivos do seu projeto.

