import argparse
import os
import sys
import datetime

from exclude_patterns import is_env_file, prune_excluded_dirs, should_exclude_file

# --- Constantes de Configuração ---
MAX_REPORT_FILE_SIZE_BYTES = 100 * 1024 * 1024 # 100 MB por arquivo de relatório
# Buffer para garantir que não ultrapasse muito o limite (evita que um arquivo pequeno quebre o limite)
# Se o próximo conteúdo (mesmo que pequeno) faria o arquivo ultrapassar o limite, cria uma nova parte
SIZE_CHECK_BUFFER_BYTES = 50 * 1024 # 50 KB de buffer

TEXT_EXTENSIONS = ('.txt', '.php', '.js', '.jsx', '.json', '.xml', '.html', '.css',
                   '.md', '.yml', '.yaml', '.conf', '.log', '.csv', '.tsv',
                   '.ini', '.sh', '.py', '.rb', '.java', '.c', '.cpp', '.h', '.hpp',
                   '.ts', '.tsx', '.vue', '.go', '.rs', '.swift', '.kt', '.sql')
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
# --- Fim das Constantes ---


def higienizar_env(filepath):
    """
    Lê um arquivo .env, extrai apenas as chaves e oculta os valores.
    """
    linhas_higienizadas = []

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            linhas_higienizadas.append(f"--- INÍCIO DO ARQUIVO HIGIENIZADO: {filepath} ---")

            for linha in f:
                linha = linha.strip()
                # Pula linhas vazias ou comentários puros
                if not linha or linha.startswith('#'):
                    continue

                # Se tem o sinal de '=', separa a chave do valor
                if '=' in linha:
                    chave = linha.split('=', 1)[0].strip()
                    # Adiciona a chave e um aviso de que o valor foi removido
                    linhas_higienizadas.append(f"{chave}=[OCULTADO_POR_SEGURANCA]")
                else:
                    # Caso seja um export solto sem valor (ex: em scripts bash)
                    linhas_higienizadas.append(linha)

            linhas_higienizadas.append("--- FIM DO ARQUIVO ---")

    except Exception as e:
        return f"Erro ao ler {filepath}: {str(e)}"

    return "\n".join(linhas_higienizadas)


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


def get_report_file_path(output_dir, part_number, nome_projeto):
    """Gera o caminho completo para uma parte do arquivo de relatório."""
    return os.path.join(output_dir, f"conteudo_parte{part_number}_{nome_projeto}.txt")


def _build_content_block_for_file(file_path, file_name):
    """Monta o texto a ser gravado no relatório para um único arquivo."""
    base_name = os.path.basename(file_path)
    _, file_extension = os.path.splitext(file_name)
    file_extension = file_extension.lower()

    if is_env_file(file_name):
        sanitized_env = higienizar_env(file_path)
        if not sanitized_env.endswith('\n'):
            sanitized_env += '\n'
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
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                file_content = f.read()
                if not file_content.endswith('\n'):
                    file_content += '\n'

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
            f"[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. Tamanho: {file_size / (1024*1024):.2f} MB]\n"
            f"--- Fim do resumo de {base_name} ---\n\n"
        )
    except OSError as e:
        return (
            f"--- Caminho do arquivo (OUTRO TIPO): {file_path} ---\n"
            f"[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. Erro ao obter tamanho: {e}]\n"
            f"--- Fim do resumo de {base_name} ---\n\n"
        )


def scan_folder_and_report_split(folder_path, recursive=False):
    """
    Escaneia uma pasta e salva o relatório em múltiplos arquivos, cada um com tamanho máximo.
    Por padrão só inclui arquivos na raiz de folder_path; use recursive=True para toda a árvore.
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

    # --- Gerenciamento de Arquivos de Relatório ---
    current_part_number = 1
    report_file = None # Inicializa como None

    def open_new_report_part():
        nonlocal report_file, current_part_number
        if report_file:
            report_file.close() # Fecha o arquivo atual antes de abrir um novo
            print(f"Parte do relatório concluída: {report_file.name}")

        report_file_path = get_report_file_path(output_dir, current_part_number, nome_projeto)
        report_file = open(report_file_path, 'w', encoding='utf-8')

        report_file.write(f"--- Relatório de Escaneamento de Pasta (Parte {current_part_number}): {folder_path} ---\n")
        report_file.write(f"{modo_relatorio}\n")
        report_file.write(f"Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_file.write(f"Tamanho máximo por parte: {MAX_REPORT_FILE_SIZE_BYTES / (1024*1024):.0f} MB.\n")
        report_file.write("-------------------------------------------------------------------\n\n")
        print(f"Abrindo nova parte do relatório: {report_file_path}")

    # Abre a primeira parte do relatório
    open_new_report_part()
    # --- Fim do Gerenciamento de Arquivos ---

    print(f"Iniciando escaneamento da pasta: {folder_path}")
    print(modo_relatorio)
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
        content_to_write = _build_content_block_for_file(file_path, file_name)

        content_bytes_length = len(content_to_write.encode('utf-8'))
        if (report_file.tell() + content_bytes_length) > (MAX_REPORT_FILE_SIZE_BYTES - SIZE_CHECK_BUFFER_BYTES):
            current_part_number += 1
            open_new_report_part()

        report_file.write(content_to_write)

    # Garante que a última parte do relatório seja fechada
    if report_file:
        report_file.write("-------------------------------------------------------------------\n")
        report_file.write("Escaneamento concluído.\n")
        report_file.close()
        print(f"Parte final do relatório concluída: {report_file.name}")

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
        "-r",
        "--recursive",
        action="store_true",
        help="Incluir subpastas (padrão: só arquivos na raiz da pasta)",
    )
    args = parser.parse_args(argv)
    scan_folder_and_report_split(os.path.abspath(args.pasta), recursive=args.recursive)


if __name__ == "__main__":
    main()
