import argparse
import datetime
import os
import re
import sys

from exclude_patterns import is_env_file, prune_excluded_dirs, should_exclude_file

# --- Constantes de Configuração ---
# Modo --php (Markdown / XML, Notebook LM)
MAX_REPORT_FILE_SIZE_BYTES = 5 * 1024 * 1024 # 5 MB por arquivo de relatório
# Modo padrão (legacy .txt, igual espírito à branch f9b0bf7)
LEGACY_MAX_REPORT_FILE_SIZE_BYTES = 100 * 1024 * 1024 # 100 MB por arquivo de relatório
# Buffer para garantir que não ultrapasse muito o limite (evita que um arquivo pequeno quebre o limite)
# Se o próximo conteúdo (mesmo que pequeno) faria o arquivo ultrapassar o limite, cria uma nova parte
SIZE_CHECK_BUFFER_BYTES = 50 * 1024 # 50 KB de buffer

# Extensão -> identificador de linguagem para cerca Markdown ```lang
EXT_TO_FENCE_LANG = {
    '.txt': 'text',
    '.php': 'php',
    '.phtml': 'php',
    '.js': 'javascript',
    '.jsx': 'javascript',
    '.json': 'json',
    '.xml': 'xml',
    '.html': 'html',
    '.css': 'css',
    '.md': 'markdown',
    '.yml': 'yaml',
    '.yaml': 'yaml',
    '.conf': 'ini',
    '.log': 'text',
    '.csv': 'csv',
    '.tsv': 'csv',
    '.ini': 'ini',
    '.sh': 'bash',
    '.py': 'python',
    '.rb': 'ruby',
    '.java': 'java',
    '.c': 'c',
    '.cpp': 'cpp',
    '.h': 'c',
    '.hpp': 'cpp',
    '.ts': 'typescript',
    '.tsx': 'tsx',
    '.vue': 'vue',
    '.go': 'go',
    '.rs': 'rust',
    '.swift': 'swift',
    '.kt': 'kotlin',
    '.lock': 'text',
}

TEXT_EXTENSIONS = ('.txt', '.php', '.phtml', '.js', '.jsx', '.json', '.xml', '.html', '.css',
                   '.md', '.yml', '.yaml', '.conf', '.log', '.csv', '.tsv',
                   '.ini', '.sh', '.py', '.rb', '.java', '.c', '.cpp', '.h', '.hpp',
                   '.ts', '.tsx', '.vue', '.go', '.rs', '.swift', '.kt')
TEXT_FILENAMES_NO_EXT = ('Dockerfile', 'Makefile', 'LICENSE', 'README', 'CHANGELOG',
                         'package.json', 'yarn.lock', 'pnpm-lock.yaml', 'composer.json',
                         'Gemfile', 'Rakefile', '.gitignore', '.gitattributes', '.editorconfig')
BINARY_EXTENSIONS = ('.zip', '.gz', '.tar', '.rar', '.7z', '.bz2', '.tgz', '.mp3',
                     '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.ogg',
                     '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.ico', '.svg',
                     '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                     '.odt', '.ods', '.odp', '.bin', '.exe', '.dll', '.so', '.o',
                     '.class', '.jar', '.apk', '.iso', '.img', '.dmg', '.vmdk',
                     '.sqlite', '.db', '.dat', '.mdb', '.accdb', '.bak', '.tmp',
                     '.swp', '.swo', '.pyc', '.pyo', '.lock')

PHP_EXTENSIONS = ('.php', '.phtml')

# Tokens no export Markdown NLM-friendly (sanitizadores costumam cortar `<?=` / short open).
# A sequência `<?php` é omitida do texto exportado em modo NLM (ver `_remove_php_open_tags_for_nlm`).
NLM_PHP_ECHO_TOKEN = "__NLM_PHP_ECHO_OPEN__"
NLM_PHP_SHORT_TOKEN = "__NLM_PHP_SHORT_OPEN__"

# Caracteres zero-width que devem ser removidos do conteúdo antes de gravar.
_ZERO_WIDTH = frozenset({"\u200b", "\u200c", "\u200d", "\u2060", "\ufeff"})
# --- Fim das Constantes ---


def _sanitize_text(s):
    """
    Remove caracteres invisíveis problemáticos para contexto de LLM:
    - NBSP (U+00A0) -> espaço comum
    - BOM (U+FEFF) inicial -> removido
    - Zero-width (U+200B/200C/200D/2060/FEFF) -> removidos
    - Controle C0/C1 (exceto \\n e \\t) -> removidos
    """
    if not s:
        return s
    if s.startswith("\ufeff"):
        s = s.lstrip("\ufeff")
    s = s.replace("\u00a0", " ")
    out = []
    for ch in s:
        if ch in _ZERO_WIDTH:
            continue
        if ch == "\n" or ch == "\t":
            out.append(ch)
            continue
        code = ord(ch)
        if code < 0x20 or 0x7f <= code <= 0x9f:
            continue
        out.append(ch)
    return "".join(out)


def _force_php_prefix(content, file_extension):
    """Garante que arquivos PHP comecem com a tag <?php."""
    if file_extension not in PHP_EXTENSIONS:
        return content
    if content.lstrip().startswith("<?php"):
        return content
    return "<?php\n" + content


def _remove_php_open_tags_for_nlm(body):
    """Remove todas as ocorrências literais `<?php` (e espaços em branco logo a seguir) do export NLM."""
    if not body:
        return body
    return re.sub(r"<\?php\s*", "", body)


def _mask_php_for_nlm(body):
    """
    Substitui aberturas PHP restantes por tokens (após remover `<?php`).
    Ordem: `<?=` antes de short open `<?` + whitespace.
    """
    if not body:
        return body
    out = body.replace("<?=", NLM_PHP_ECHO_TOKEN)
    out = re.sub(r"<\?(?=\s)", NLM_PHP_SHORT_TOKEN, out)
    return out


def _nlm_md_preamble(nlm_friendly=True, nl_plain=False, split_role=None):
    """
    Texto Markdown repetido no início de cada parte do relatório (modo MD).
    split_role: None | 'other' | 'php' — explica o par conteudo_*.md / conteudo_php_*.md.
    """
    parts = ["## Nota para ingestão (Notebook LM e similares)\n\n"]
    if split_role == "other":
        parts.append(
            "**Ficheiro geral:** aqui entram os ficheiros **que não são** `.php` nem `.phtml`. "
            "O código **PHP** do projecto está em **`conteudo_php_*.md`** (mesma pasta de saída); este ficheiro "
            "é a série **`conteudo_projeto_*`**.\n\n"
        )
    elif split_role == "php":
        parts.append(
            "**Ficheiro só PHP:** aqui entram **apenas** ficheiros `.php` e `.phtml`. "
            "O restante (JavaScript, Go, `.env`, etc.) está em **`conteudo_projeto_*.md`** na mesma pasta de execução.\n\n"
        )
    if nl_plain:
        parts.append(
            "Com **`--nl-plain`**, **todos** os ficheiros usam formato **plano** (sem cercas ```): após cada "
            "`# Arquivo:` o conteúdo fica entre `---------- inicio-corpo ----------` e "
            "`---------- fim-corpo ----------`, com cada linha prefixada com `| `.\n\n"
        )
    elif nlm_friendly:
        parts.append(
            "**Formato misto:** ficheiros **`.php` / `.phtml`** ou outros tipos em que o conteúdo sugira **PHP "
            "embutido** (detecção por `<?php`, `<?=` ou short `<?` + espaço, excluindo `<?xml`) usam o mesmo "
            "formato plano (separadores `---------- inicio-corpo ----------` / `---------- fim-corpo ----------` "
            "e prefixo `| ` por linha, sem cercas ```). As **outras** linguagens mantêm cercas Markdown "
            "`` ```lang `` … `` ``` ``.\n\n"
        )
    if nlm_friendly:
        parts.append(
            "Nos blocos tratados como **PHP para NLM** (extensão ou conteúdo):\n\n"
            "- A sequência **`<?php` foi omitida** do texto exportado (o arquivo continua sendo PHP; "
            "assuma abertura padrão onde fizer sentido ao analisar).\n"
            "- As seguintes sequências foram **substituídas por tokens**:\n\n"
            f"  - `{NLM_PHP_ECHO_TOKEN}` → short echo (`<?=`)\n"
            f"  - `{NLM_PHP_SHORT_TOKEN}` → short open (`<?` seguido de espaço em branco)\n\n"
        )
    elif nl_plain:
        parts.append(
            "Com `--raw-php`, o conteúdo PHP é **literal** (inclui `<?php` se existir no ficheiro).\n\n"
        )
    parts.append("---\n\n")
    return "".join(parts)


def _fence_wrap(lang, inner):
    """Envolve o corpo em cerca Markdown; inner deve terminar com newline."""
    body = inner if inner.endswith("\n") else inner + "\n"
    return f"```{lang}\n{body}```\n\n"


def _xml_escape_attr(value):
    """Escapa valor para uso como atributo XML entre aspas duplas."""
    return (
        value.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace('"', "&quot;")
    )


def _build_md_block(file_path, lang, body):
    """Bloco no modo Markdown: header `# Arquivo:` + cerca ```lang."""
    header = f"# Arquivo: {file_path}\n\n"
    return header + _fence_wrap(lang, body)


def _build_md_block_plain(file_path, lang, body):
    """
    Bloco Markdown sem cercas ``` (export plano para ingestores que removem fences).
    Corpo com cada linha prefixada por '| '.
    """
    header = f"# Arquivo: {file_path}\n\n"
    body = body if body.endswith("\n") else body + "\n"
    lines = body.splitlines(keepends=True)
    prefixed = []
    for line in lines:
        if line.endswith("\n"):
            core = line[:-1]
            suff = "\n"
        else:
            core, suff = line, ""
        prefixed.append(f"| {core}{suff}")
    inner = "".join(prefixed)
    return (
        f"{header}"
        "---------- inicio-corpo ----------\n"
        f"{inner}"
        "---------- fim-corpo ----------\n\n"
    )


def _build_xml_block(file_path, body):
    """Bloco no modo XML: <file path=\"...\"> corpo cru </file>."""
    attr = _xml_escape_attr(file_path)
    body = body if body.endswith("\n") else body + "\n"
    return f'<file path="{attr}">\n{body}</file>\n\n'


def fence_lang_for_file_name(file_name):
    """Identificador de linguagem para ```lang com base no nome do arquivo."""
    ext = os.path.splitext(file_name)[1].lower()
    base = os.path.basename(file_name)
    lower = base.lower()
    if ext == "":
        if lower == "dockerfile":
            return "dockerfile"
        if lower == "makefile":
            return "makefile"
        if lower in ("gemfile", "rakefile"):
            return "ruby"
        if lower == "license":
            return "text"
        if lower == "readme":
            return "text"
        if lower == "changelog":
            return "text"
        if lower == ".gitignore":
            return "gitignore"
        if lower == ".gitattributes":
            return "gitattributes"
        if lower == ".editorconfig":
            return "editorconfig"
        return "text"
    return EXT_TO_FENCE_LANG.get(ext, "text")


def _read_env_sanitized_body(filepath):
    """
    Lê .env / .env.*: só chaves, valores mascarados (para cercas no relatório).
    """
    linhas_out = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue
                if "=" in linha:
                    chave = linha.split("=", 1)[0].strip()
                    linhas_out.append(f"{chave}=[OCULTADO_POR_SEGURANCA]")
                else:
                    linhas_out.append(linha)
        body = "\n".join(linhas_out) + ("\n" if linhas_out else "\n")
        return _sanitize_text(body)
    except Exception as e:
        return f"Erro ao ler {filepath}: {str(e)}\n"


def higienizar_env(filepath):
    """
    Lê um arquivo .env, extrai apenas as chaves e oculta os valores (formato legacy .txt).
    """
    linhas_higienizadas = []

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            linhas_higienizadas.append(f"--- INÍCIO DO ARQUIVO HIGIENIZADO: {filepath} ---")

            for linha in f:
                linha = linha.strip()
                if not linha or linha.startswith("#"):
                    continue

                if "=" in linha:
                    chave = linha.split("=", 1)[0].strip()
                    linhas_higienizadas.append(f"{chave}=[OCULTADO_POR_SEGURANCA]")
                else:
                    linhas_higienizadas.append(linha)

            linhas_higienizadas.append("--- FIM DO ARQUIVO ---")

    except Exception as e:
        return f"Erro ao ler {filepath}: {str(e)}"

    return "\n".join(linhas_higienizadas)


def _content_suggests_embedded_php(content):
    """
    Heurística conservadora (prefixo do ficheiro): PHP embutido em .html, .vue, etc.
    Evita tratar declarações XML como PHP (<?xml ...>).
    """
    if not content:
        return False
    head = content[:65536]
    if "<?php" in head or "<?=" in head:
        return True
    # Short open `<?` + espaço em branco, excluindo `<?xml`
    return bool(re.search(r"<\?(?!xml)(?=\s)", head))


def preparar_pasta_de_saida(caminho_projeto):
    """
    Cria uma pasta organizada para salvar os relatórios da execução atual.
    Retorna o caminho absoluto dessa nova pasta.
    """
    nome_projeto = os.path.basename(os.path.normpath(caminho_projeto))
    if not nome_projeto:
        nome_projeto = "projeto_desconhecido"

    nome_projeto = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in nome_projeto)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_pasta_execucao = f"relatorio_{nome_projeto}_{timestamp}"

    diretorio_do_script = os.path.dirname(os.path.abspath(__file__))
    caminho_saida = os.path.join(diretorio_do_script, "relatorios", nome_pasta_execucao)
    os.makedirs(caminho_saida, exist_ok=True)
    return caminho_saida, nome_projeto


def _file_is_php_extension(file_name):
    """True só para extensões .php / .phtml (ficheiros PHP no relatório dedicado)."""
    return os.path.splitext(file_name)[1].lower() in PHP_EXTENSIONS


def _stream_part_path_modern(output_dir, nome_projeto, fmt, php_stream, part_number):
    """Caminho de uma parte do relatório no modo LM: `conteudo_projeto_*` vs `conteudo_php_*` (globs sem ambiguidade)."""
    ext = "xml" if fmt == "xml" else "md"
    if php_stream:
        if part_number == 1:
            return os.path.join(output_dir, f"conteudo_php_{nome_projeto}.{ext}")
        return os.path.join(output_dir, f"conteudo_php_{part_number}_{nome_projeto}.{ext}")
    if part_number == 1:
        return os.path.join(output_dir, f"conteudo_projeto_{nome_projeto}.{ext}")
    return os.path.join(output_dir, f"conteudo_projeto_{part_number}_{nome_projeto}.{ext}")


def _stream_part_path_legacy(output_dir, nome_projeto, php_stream, part_number):
    """Caminho legacy (.txt): `conteudo_projeto_*` vs `conteudo_php_*`."""
    if php_stream:
        if part_number == 1:
            return os.path.join(output_dir, f"conteudo_php_{nome_projeto}.txt")
        return os.path.join(output_dir, f"conteudo_php_{part_number}_{nome_projeto}.txt")
    if part_number == 1:
        return os.path.join(output_dir, f"conteudo_projeto_{nome_projeto}.txt")
    return os.path.join(output_dir, f"conteudo_projeto_{part_number}_{nome_projeto}.txt")


def _wrap_block(file_path, body, lang, fmt, nlm_friendly=False, nl_plain=False, php_nlm_for_body=False):
    """Dispatcher: MD+NLM com formato plano quando php_nlm_for_body; nl_plain força plano para todas."""
    if fmt == "xml":
        return _build_xml_block(file_path, body)
    if nlm_friendly and php_nlm_for_body:
        body = _remove_php_open_tags_for_nlm(body)
        body = _mask_php_for_nlm(body)
    use_plain = nl_plain or (nlm_friendly and php_nlm_for_body)
    if use_plain:
        return _build_md_block_plain(file_path, lang, body)
    return _build_md_block(file_path, lang, body)


def _build_content_block_for_file(file_path, file_name, fmt, nlm_friendly=False, nl_plain=False):
    """Monta o texto a ser gravado no relatório para um único arquivo no formato escolhido."""
    file_path = os.path.abspath(file_path)
    base_name = os.path.basename(file_path)
    _, file_extension = os.path.splitext(file_name)
    file_extension = file_extension.lower()

    if is_env_file(file_name):
        body = _read_env_sanitized_body(file_path)
        lang = "text" if body.startswith("Erro ao ler") else "dotenv"
        return _wrap_block(
            file_path, body, lang, fmt,
            nlm_friendly=nlm_friendly, nl_plain=nl_plain, php_nlm_for_body=False,
        )

    if file_extension in BINARY_EXTENSIONS:
        try:
            file_size = os.path.getsize(file_path)
            msg = (
                "[Conteúdo não exibido: Arquivo binário conhecido. "
                f"Tamanho: {file_size / (1024*1024):.2f} MB]\n"
            )
        except OSError as e:
            msg = (
                "[Conteúdo não exibido: Arquivo binário conhecido. "
                f"Erro ao obter tamanho: {e}]\n"
            )
        return _wrap_block(
            file_path, msg, "text", fmt,
            nlm_friendly=nlm_friendly, nl_plain=nl_plain, php_nlm_for_body=False,
        )

    if base_name in TEXT_FILENAMES_NO_EXT or file_extension in TEXT_EXTENSIONS:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()
            file_content = _sanitize_text(file_content)
            nlm_md = fmt == "md" and nlm_friendly
            php_nlm_for_body = nlm_md and (
                file_extension in PHP_EXTENSIONS
                or _content_suggests_embedded_php(file_content)
            )
            if not (file_extension in PHP_EXTENSIONS and php_nlm_for_body):
                file_content = _force_php_prefix(file_content, file_extension)
            if not file_content.endswith("\n"):
                file_content += "\n"
            lang = fence_lang_for_file_name(file_name)
            return _wrap_block(
                file_path, file_content, lang, fmt,
                nlm_friendly=nlm_friendly, nl_plain=nl_plain, php_nlm_for_body=php_nlm_for_body,
            )
        except OSError as e:
            return _wrap_block(
                file_path, f"[ERRO AO ACESSAR ARQUIVO: {e}]\n", "text", fmt,
                nlm_friendly=nlm_friendly, nl_plain=nl_plain, php_nlm_for_body=False,
            )
        except Exception as e:
            return _wrap_block(
                file_path, f"[ERRO AO LER CONTEÚDO: {e}]\n", "text", fmt,
                nlm_friendly=nlm_friendly, nl_plain=nl_plain, php_nlm_for_body=False,
            )

    try:
        file_size = os.path.getsize(file_path)
        msg = (
            "[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. "
            f"Tamanho: {file_size / (1024*1024):.2f} MB]\n"
        )
    except OSError as e:
        msg = (
            "[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. "
            f"Erro ao obter tamanho: {e}]\n"
        )
    return _wrap_block(
        file_path, msg, "text", fmt,
        nlm_friendly=nlm_friendly, nl_plain=nl_plain, php_nlm_for_body=False,
    )


def _build_content_block_for_file_legacy(file_path, file_name):
    """Relatório legacy (.txt): delimitadores --- como na branch f9b0bf7."""
    file_path = os.path.abspath(file_path)
    base_name = os.path.basename(file_path)
    _, file_extension = os.path.splitext(file_name)
    file_extension = file_extension.lower()

    if is_env_file(file_name):
        sanitized_env = higienizar_env(file_path)
        if not sanitized_env.endswith("\n"):
            sanitized_env += "\n"
        return (
            f"--- Caminho do arquivo (ENV HIGIENIZADO): {file_path} ---\n"
            f"{sanitized_env}"
            f"--- Fim do conteúdo higienizado de {base_name} ---\n\n"
        )

    if file_extension in BINARY_EXTENSIONS:
        try:
            file_size = os.path.getsize(file_path)
            return (
                f"--- Caminho do arquivo (BINÁRIO): {file_path} ---\n"
                f"[Conteúdo não exibido: Arquivo binário conhecido. Tamanho: {file_size / (1024*1024):.2f} MB]\n"
                f"--- Fim do resumo de {base_name} ---\n\n"
            )
        except OSError as e:
            return (
                f"--- Caminho do arquivo (BINÁRIO): {file_path} ---\n"
                f"[Conteúdo não exibido: Arquivo binário conhecido. Erro ao obter tamanho: {e}]\n"
                f"--- Fim do resumo de {base_name} ---\n\n"
            )

    if base_name in TEXT_FILENAMES_NO_EXT or file_extension in TEXT_EXTENSIONS:
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()
            if not file_content.endswith("\n"):
                file_content += "\n"
            return (
                f"--- Caminho do arquivo (TEXTO): {file_path} ---\n"
                f"{file_content}"
                f"--- Fim do conteúdo de {base_name} ---\n\n"
            )
        except OSError as e:
            return (
                f"--- Caminho do arquivo (TEXTO): {file_path} ---\n"
                f"[ERRO AO ACESSAR ARQUIVO: {e}]\n"
                f"--- Fim do conteúdo de {base_name} ---\n\n"
            )
        except Exception as e:
            return (
                f"--- Caminho do arquivo (TEXTO): {file_path} ---\n"
                f"[ERRO AO LER CONTEÚDO: {e}]\n"
                f"--- Fim do conteúdo de {base_name} ---\n\n"
            )

    try:
        file_size = os.path.getsize(file_path)
        return (
            f"--- Caminho do arquivo (OUTRO TIPO): {file_path} ---\n"
            f"[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. "
            f"Tamanho: {file_size / (1024*1024):.2f} MB]\n"
            f"--- Fim do resumo de {base_name} ---\n\n"
        )
    except OSError as e:
        return (
            f"--- Caminho do arquivo (OUTRO TIPO): {file_path} ---\n"
            f"[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. Erro ao obter tamanho: {e}]\n"
            f"--- Fim do resumo de {base_name} ---\n\n"
        )


def _write_report_header(
    report_file,
    fmt,
    part_number,
    folder_path,
    modo_relatorio,
    nlm_friendly=False,
    nl_plain=False,
    max_size_bytes=None,
    split_role=None,
    legacy_stream_note=None,
):
    """Escreve o cabeçalho do relatório (com coment. XML se modo xml) e abre <files> se aplicável."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    size_b = max_size_bytes if max_size_bytes is not None else MAX_REPORT_FILE_SIZE_BYTES
    max_mb = size_b / (1024 * 1024)
    if fmt == "xml":
        report_file.write(f"<!-- Relatório de Escaneamento de Pasta (Parte {part_number}): {folder_path} -->\n")
        report_file.write(f"<!-- {modo_relatorio} -->\n")
        report_file.write(f"<!-- Gerado em: {timestamp} -->\n")
        report_file.write(f"<!-- Tamanho máximo por parte: {max_mb:.0f} MB. -->\n")
        if split_role == "php":
            report_file.write("<!-- Montagem: apenas ficheiros .php e .phtml -->\n")
        elif split_role == "other":
            report_file.write("<!-- Montagem: ficheiros excepto .php e .phtml -->\n")
        report_file.write("<files>\n")
    else:
        report_file.write(f"--- Relatório de Escaneamento de Pasta (Parte {part_number}): {folder_path} ---\n")
        report_file.write(f"{modo_relatorio}\n")
        report_file.write(f"Gerado em: {timestamp}\n")
        report_file.write(f"Tamanho máximo por parte: {max_mb:.0f} MB.\n")
        if legacy_stream_note:
            report_file.write(f"{legacy_stream_note}\n")
        report_file.write("-------------------------------------------------------------------\n\n")
        if nlm_friendly or nl_plain:
            report_file.write(
                _nlm_md_preamble(nlm_friendly=nlm_friendly, nl_plain=nl_plain, split_role=split_role)
            )


def _write_report_footer(report_file, fmt):
    """Escreve o rodapé do relatório (fechando <files> no modo xml)."""
    if fmt == "xml":
        report_file.write("</files>\n")
        report_file.write("<!-- Escaneamento concluído. -->\n")
    else:
        report_file.write("-------------------------------------------------------------------\n")
        report_file.write("Escaneamento concluído.\n")


def _stream_state(is_php):
    """Estado de um fluxo de relatório (principal vs só PHP)."""
    return {"fp": None, "part": 1, "is_php": is_php}


def _legacy_stream_note(is_php):
    if is_php:
        return "Montagem desta parte: apenas ficheiros .php e .phtml."
    return "Montagem desta parte: ficheiros excepto .php e .phtml."


def _stream_roll_and_open_modern(
    st, output_dir, nome_projeto, fmt, folder_path, modo_relatorio, nlm_effective, nl_plain_effective, max_bytes,
):
    if st["fp"] is not None:
        old_path = st["fp"].name
        _write_report_footer(st["fp"], fmt)
        st["fp"].close()
        print(f"Parte do relatório concluída: {old_path}")
        st["part"] += 1
        if st["part"] == 2:
            ext = "xml" if fmt == "xml" else "md"
            if st["is_php"]:
                dest = os.path.join(output_dir, f"conteudo_php_1_{nome_projeto}.{ext}")
            else:
                dest = os.path.join(output_dir, f"conteudo_projeto_1_{nome_projeto}.{ext}")
            os.rename(old_path, dest)
    path = _stream_part_path_modern(output_dir, nome_projeto, fmt, st["is_php"], st["part"])
    role = "php" if st["is_php"] else "other"
    st["fp"] = open(path, "w", encoding="utf-8")
    _write_report_header(
        st["fp"], fmt, st["part"], folder_path, modo_relatorio,
        nlm_friendly=nlm_effective, nl_plain=nl_plain_effective,
        max_size_bytes=max_bytes,
        split_role=role,
    )
    print(f"Abrindo nova parte do relatório: {path}")


def _stream_roll_and_open_legacy(st, output_dir, nome_projeto, folder_path, modo_relatorio, max_bytes):
    if st["fp"] is not None:
        old_path = st["fp"].name
        st["fp"].write("-------------------------------------------------------------------\n")
        st["fp"].write("Escaneamento concluído.\n")
        st["fp"].close()
        print(f"Parte do relatório concluída: {old_path}")
        st["part"] += 1
        if st["part"] == 2:
            if st["is_php"]:
                dest = os.path.join(output_dir, f"conteudo_php_1_{nome_projeto}.txt")
            else:
                dest = os.path.join(output_dir, f"conteudo_projeto_1_{nome_projeto}.txt")
            os.rename(old_path, dest)
    path = _stream_part_path_legacy(output_dir, nome_projeto, st["is_php"], st["part"])
    st["fp"] = open(path, "w", encoding="utf-8")
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st["fp"].write(f"--- Relatório de Escaneamento de Pasta (Parte {st['part']}): {folder_path} ---\n")
    st["fp"].write(f"{modo_relatorio}\n")
    st["fp"].write(f"Gerado em: {ts}\n")
    st["fp"].write(f"Tamanho máximo por parte: {max_bytes / (1024*1024):.0f} MB.\n")
    st["fp"].write(f"{_legacy_stream_note(st['is_php'])}\n")
    st["fp"].write("-------------------------------------------------------------------\n\n")
    print(f"Abrindo nova parte do relatório: {path}")


def _stream_write_modern(
    st, content, output_dir, nome_projeto, fmt, folder_path, modo_relatorio, nlm_effective, nl_plain_effective, max_bytes,
):
    chunk = content.encode("utf-8")
    n = len(chunk)
    threshold = max_bytes - SIZE_CHECK_BUFFER_BYTES
    if st["fp"] is None:
        _stream_roll_and_open_modern(
            st, output_dir, nome_projeto, fmt, folder_path, modo_relatorio, nlm_effective, nl_plain_effective, max_bytes,
        )
    elif st["fp"].tell() + n > threshold:
        _stream_roll_and_open_modern(
            st, output_dir, nome_projeto, fmt, folder_path, modo_relatorio, nlm_effective, nl_plain_effective, max_bytes,
        )
    st["fp"].write(content)


def _stream_write_legacy(st, content, output_dir, nome_projeto, folder_path, modo_relatorio, max_bytes):
    chunk = content.encode("utf-8")
    n = len(chunk)
    threshold = max_bytes - SIZE_CHECK_BUFFER_BYTES
    if st["fp"] is None:
        _stream_roll_and_open_legacy(st, output_dir, nome_projeto, folder_path, modo_relatorio, max_bytes)
    elif st["fp"].tell() + n > threshold:
        _stream_roll_and_open_legacy(st, output_dir, nome_projeto, folder_path, modo_relatorio, max_bytes)
    st["fp"].write(content)


def _stream_close_modern(st, fmt):
    if st["fp"]:
        final_name = st["fp"].name
        _write_report_footer(st["fp"], fmt)
        st["fp"].close()
        st["fp"] = None
        print(f"Parte final do relatório concluída: {final_name}")


def _stream_close_legacy(st):
    if st["fp"]:
        final_name = st["fp"].name
        st["fp"].write("-------------------------------------------------------------------\n")
        st["fp"].write("Escaneamento concluído.\n")
        st["fp"].close()
        st["fp"] = None
        print(f"Parte final do relatório concluída: {final_name}")


def _folder_has_scannable_php_files(folder_path, recursive):
    """
    True se existir pelo menos um ficheiro .php ou .phtml que entraria no escaneamento
    (mesmas regras que should_exclude_file + prune_excluded_dirs).
    Usado para activar automaticamente o modo Markdown/NLM sem --php.
    """
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        return False
    if recursive:
        for root, dirs, files in os.walk(folder_path):
            prune_excluded_dirs(dirs)
            for file_name in files:
                if should_exclude_file(file_name, include_env_files=True, for_content_scan=True):
                    continue
                if os.path.splitext(file_name)[1].lower() in PHP_EXTENSIONS:
                    return True
        return False
    try:
        for file_name in sorted(os.listdir(folder_path)):
            file_path = os.path.join(folder_path, file_name)
            if not os.path.isfile(file_path):
                continue
            if should_exclude_file(file_name, include_env_files=True, for_content_scan=True):
                continue
            if os.path.splitext(file_name)[1].lower() in PHP_EXTENSIONS:
                return True
    except OSError:
        return False
    return False


def scan_folder_and_report_split_legacy(folder_path, recursive=False):
    """
    Relatório legacy: .txt, cabeçalhos --- Caminho do arquivo ---, 100 MB por parte
    (espírito da branch f9b0bf7). Usado quando não há modo Notebook LM ou com --legacy-only.
    """
    if not os.path.isdir(folder_path):
        print(f"Erro: O caminho '{folder_path}' não é um diretório válido.")
        return

    folder_path = os.path.abspath(folder_path)
    modo_relatorio = (
        "Modo: recursivo (toda a árvore de subpastas)"
        if recursive
        else "Modo: somente raiz (apenas arquivos diretos nesta pasta, sem subpastas)"
    )

    output_dir, nome_projeto = preparar_pasta_de_saida(folder_path)

    max_bytes = LEGACY_MAX_REPORT_FILE_SIZE_BYTES
    st_other = _stream_state(False)
    st_php = _stream_state(True)

    print(f"Iniciando escaneamento da pasta: {folder_path}")
    print(modo_relatorio)
    print(
        "Formato de saída: texto legacy (.txt); `.php`/`.phtml` em `conteudo_php_*.txt`, "
        "demais ficheiros em `conteudo_projeto_*.txt` (mesma pasta)."
    )
    print(f"Os arquivos gerados serão salvos em: {output_dir}")
    print(f"O relatório será salvo em múltiplas partes (max {max_bytes / (1024*1024):.0f} MB por parte).")
    print("-----------------------------------")
    print("")

    def iter_file_jobs():
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                prune_excluded_dirs(dirs)
                for file_name in files:
                    if should_exclude_file(file_name, include_env_files=True, for_content_scan=True):
                        continue
                    yield os.path.join(root, file_name), file_name
        else:
            try:
                for file_name in sorted(os.listdir(folder_path)):
                    file_path = os.path.join(folder_path, file_name)
                    if not os.path.isfile(file_path):
                        continue
                    if should_exclude_file(file_name, include_env_files=True, for_content_scan=True):
                        continue
                    yield file_path, file_name
            except OSError as e:
                print(f"Erro ao listar a pasta raiz '{folder_path}': {e}")

    for file_path, file_name in iter_file_jobs():
        content_to_write = _build_content_block_for_file_legacy(file_path, file_name)
        st = st_php if _file_is_php_extension(file_name) else st_other
        _stream_write_legacy(st, content_to_write, output_dir, nome_projeto, folder_path, modo_relatorio, max_bytes)

    _stream_close_legacy(st_other)
    _stream_close_legacy(st_php)

    print("Escaneamento concluído.")
    print(f"Relatório(s) salvo(s) com sucesso em: {output_dir}")


def scan_folder_and_report_split(folder_path, recursive=False, fmt="md", nlm_friendly=True, nl_plain=False):
    """
    Escaneia uma pasta e salva o relatório em múltiplos arquivos, cada um com tamanho máximo.
    Por padrão só inclui arquivos na raiz de folder_path; use recursive=True para toda a árvore.
    O formato é controlado por fmt ("md" ou "xml"). Em Markdown, nlm_friendly (default True)
    aplica preâmbulo e mascaramento de aberturas PHP para ingestão (Notebook LM).
    Com nl_plain=True (só MD), todas as linguagens em formato plano. Sem nl_plain, com NLM ativo,
    Ficheiros `.php`/`.phtml` vão para a série `conteudo_php_*`; o restante para `conteudo_*`.
    Em cada série, blocos com PHP para NLM (ext. .php/.phtml ou PHP embutido no conteúdo)
    usam formato plano quando aplicável; as restantes mantêm cercas ```lang.
    """
    if not os.path.isdir(folder_path):
        print(f"Erro: O caminho '{folder_path}' não é um diretório válido.")
        return

    folder_path = os.path.abspath(folder_path)
    modo_relatorio = (
        "Modo: recursivo (toda a árvore de subpastas)"
        if recursive
        else "Modo: somente raiz (apenas arquivos diretos nesta pasta, sem subpastas)"
    )

    # --- Configuração da Pasta de Saída ---
    output_dir, nome_projeto = preparar_pasta_de_saida(folder_path)
    # --- Fim da Configuração ---

    nlm_effective = nlm_friendly and fmt == "md"
    nl_plain_effective = nl_plain and fmt == "md"
    st_other = _stream_state(False)
    st_php = _stream_state(True)

    print(f"Iniciando escaneamento da pasta: {folder_path}")
    print(modo_relatorio)
    print(f"Formato de saída: {fmt}")
    print(
        "Séries de ficheiros: `conteudo_php_*` (apenas .php/.phtml) e `conteudo_projeto_*` "
        "(restantes), na mesma pasta de saída."
    )
    if fmt == "md":
        print(f"Modo Notebook LM (máscara PHP + preâmbulo): {'sim' if nlm_effective else 'não (--raw-php)'}")
        print(
            "PHP para NLM em formato plano (.php/.phtml ou PHP embutido; com NLM, sem --raw-php): "
            f"{'sim' if nlm_effective else 'não'}"
        )
        print(f"Export plano em todas as linguagens (--nl-plain): {'sim' if nl_plain_effective else 'não'}")
    print(f"Os arquivos gerados serão salvos em: {output_dir}")
    print(f"O relatório será salvo em múltiplas partes (max {MAX_REPORT_FILE_SIZE_BYTES / (1024*1024):.0f} MB por parte).")
    print("-----------------------------------")
    print("")

    def iter_file_jobs():
        if recursive:
            for root, dirs, files in os.walk(folder_path):
                prune_excluded_dirs(dirs)
                for file_name in files:
                    if should_exclude_file(file_name, include_env_files=True, for_content_scan=True):
                        continue
                    yield os.path.join(root, file_name), file_name
        else:
            try:
                for file_name in sorted(os.listdir(folder_path)):
                    file_path = os.path.join(folder_path, file_name)
                    if not os.path.isfile(file_path):
                        continue
                    if should_exclude_file(file_name, include_env_files=True, for_content_scan=True):
                        continue
                    yield file_path, file_name
            except OSError as e:
                print(f"Erro ao listar a pasta raiz '{folder_path}': {e}")

    for file_path, file_name in iter_file_jobs():
        content_to_write = _build_content_block_for_file(
            file_path, file_name, fmt, nlm_friendly=nlm_effective, nl_plain=nl_plain_effective,
        )
        st = st_php if _file_is_php_extension(file_name) else st_other
        _stream_write_modern(
            st,
            content_to_write,
            output_dir,
            nome_projeto,
            fmt,
            folder_path,
            modo_relatorio,
            nlm_effective,
            nl_plain_effective,
            MAX_REPORT_FILE_SIZE_BYTES,
        )

    _stream_close_modern(st_other, fmt)
    _stream_close_modern(st_php, fmt)

    print("Escaneamento concluído.")
    print(f"Relatório(s) salvo(s) com sucesso em: {output_dir}")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Gera relatório de conteúdo de arquivos de um diretório.",
    )
    parser.add_argument(
        "pasta",
        help="Caminho da pasta do projeto a escanear",
    )
    parser.add_argument(
        "-php",
        "--php",
        action="store_true",
        help=(
            "Activa explicitamente o modo Notebook LM: Markdown (.md) ou XML, preâmbulo, PHP plano com máscaras, "
            "5 MB/partes. Se omitir esta flag, o mesmo modo é escolhido **automaticamente** quando o escaneamento "
            "incluir ficheiros `.php` ou `.phtml`; caso contrário gera-se legacy (.txt). Use `--legacy-only` para "
            "forçar .txt mesmo com PHP no projeto."
        ),
    )
    parser.add_argument(
        "--legacy-only",
        action="store_true",
        help=(
            "Força relatório legacy (.txt, 100 MB/partes) mesmo quando existem `.php`/`.phtml` no escopo "
            "(sem auto-activação do modo Notebook LM). Se combinar com `--php`, `--legacy-only` tem prioridade."
        ),
    )
    parser.add_argument(
        "-r",
        "-recursive",
        "--recursive",
        action="store_true",
        help="Incluir subpastas (padrão: só arquivos na raiz da pasta)",
    )
    fmt_group = parser.add_mutually_exclusive_group()
    fmt_group.add_argument(
        "-md",
        "--md",
        dest="fmt",
        action="store_const",
        const="md",
        help="Markdown (padrão) no modo Notebook LM: `# Arquivo:`; PHP plano com NLM; outras com cercas",
    )
    fmt_group.add_argument(
        "-xml",
        "--xml",
        dest="fmt",
        action="store_const",
        const="xml",
        help='XML no modo Notebook LM: tags <file path="...">...</file>',
    )
    parser.set_defaults(fmt="md")
    parser.add_argument(
        "--raw-php",
        action="store_true",
        help="Só no modo Notebook LM: desactiva preâmbulo e máscara NLM no Markdown (PHP literal nas cercas ```php)",
    )
    parser.add_argument(
        "--nl-plain",
        action="store_true",
        help=(
            "Só no modo Notebook LM: força formato plano (sem cercas ```) em **todas** as linguagens. "
            "Com NLM, por defeito só blocos PHP (ext. ou embutido) usam plano; Go/JS mantêm ```lang."
        ),
    )

    args = parser.parse_args(argv)
    folder_abs = os.path.abspath(args.pasta)

    if args.legacy_only and args.php:
        print(
            "Aviso: `--legacy-only` e `--php` foram ambos indicados; a usar apenas modo legacy (.txt).",
            file=sys.stderr,
        )

    if args.legacy_only:
        use_modern_export = False
    else:
        use_modern_export = args.php or _folder_has_scannable_php_files(folder_abs, args.recursive)

    if use_modern_export and not args.php and not args.legacy_only:
        print(
            "Detetados ficheiros .php/.phtml no escopo do escaneamento; a usar export Markdown (modo Notebook LM). "
            "Para forçar .txt use `--legacy-only`."
        )

    if args.fmt == "xml" and not use_modern_export:
        print(
            "Erro: exportação XML só está disponível no modo Notebook LM (use `--php` ou inclua `.php`/`.phtml` "
            "no escopo, ou remova `--legacy-only`). O modo legacy gera apenas .txt.",
            file=sys.stderr,
        )
        sys.exit(2)

    if not use_modern_export:
        if args.raw_php:
            print("Aviso: --raw-php só tem efeito no modo Notebook LM (.md); a ignorar.", file=sys.stderr)
        if args.nl_plain:
            print("Aviso: --nl-plain só tem efeito no modo Notebook LM (.md); a ignorar.", file=sys.stderr)
        scan_folder_and_report_split_legacy(
            folder_abs,
            recursive=args.recursive,
        )
        return

    nlm_friendly = not args.raw_php
    if args.raw_php and args.fmt == "xml":
        print("Aviso: --raw-php só afeta export Markdown; modo -xml inalterado.")
    if args.nl_plain and args.fmt == "xml":
        print("Aviso: --nl-plain só se aplica ao Markdown; modo -xml inalterado.")

    scan_folder_and_report_split(
        folder_abs,
        recursive=args.recursive,
        fmt=args.fmt,
        nlm_friendly=nlm_friendly,
        nl_plain=args.nl_plain,
    )


if __name__ == "__main__":
    main()
