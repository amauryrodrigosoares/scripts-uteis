import os
import sys
import datetime

# --- Constantes de Configuração ---
MAX_REPORT_FILE_SIZE_BYTES = 185 * 1024 * 1024 # 185 MB por arquivo de relatório
# Buffer para garantir que não ultrapasse muito o limite (evita que um arquivo pequeno quebre o limite)
# Se o próximo conteúdo (mesmo que pequeno) faria o arquivo ultrapassar o limite, cria uma nova parte
SIZE_CHECK_BUFFER_BYTES = 50 * 1024 # 50 KB de buffer

TEXT_EXTENSIONS = ('.txt', '.php', '.js', '.jsx', '.json', '.xml', '.html', '.css', 
                   '.md', '.yml', '.yaml', '.conf', '.log', '.csv', '.tsv', 
                   '.ini', '.sh', '.py', '.rb', '.java', '.c', '.cpp', '.h', '.hpp',
                   '.ts', '.tsx', '.vue', '.go', '.rs', '.swift', '.kt', '.sql')
TEXT_FILENAMES_NO_EXT = ('Dockerfile', '.env', 'Makefile', 'LICENSE', 'README', 'CHANGELOG',
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

def get_report_file_path(base_name, part_number, script_dir):
    """Gera o caminho completo para uma parte do arquivo de relatório."""
    return os.path.join(script_dir, f"{base_name}-parte{part_number}.txt")

def scan_folder_and_report_split(folder_path):
    """
    Escaneia uma pasta e salva o relatório em múltiplos arquivos, cada um com tamanho máximo.
    Exibe o conteúdo apenas para arquivos de texto específicos, ignorando binários.
    """
    if not os.path.isdir(folder_path):
        print(f"Erro: O caminho '{folder_path}' não é um diretório válido.")
        return

    # --- Configuração do Nome Base do Relatório ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    safe_folder_name = os.path.normpath(folder_path).replace(os.sep, '-').strip('-')
    safe_folder_name = ''.join(c if c.isalnum() or c in ['-', '_'] else '_' for c in safe_folder_name)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_name_base = f"scan-report-{safe_folder_name}-{timestamp}"
    # --- Fim da Configuração ---

    # --- Gerenciamento de Arquivos de Relatório ---
    current_part_number = 1
    report_file = None # Inicializa como None
    
    def open_new_report_part():
        nonlocal report_file, current_part_number
        if report_file:
            report_file.close() # Fecha o arquivo atual antes de abrir um novo
            print(f"Parte do relatório concluída: {report_file.name}")

        report_file_path = get_report_file_path(report_name_base, current_part_number, script_dir)
        report_file = open(report_file_path, 'w', encoding='utf-8')
        
        report_file.write(f"--- Relatório de Escaneamento de Pasta (Parte {current_part_number}): {folder_path} ---\n")
        report_file.write(f"Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_file.write(f"Tamanho máximo por parte: {MAX_REPORT_FILE_SIZE_BYTES / (1024*1024):.0f} MB.\n")
        report_file.write("-------------------------------------------------------------------\n\n")
        print(f"Abrindo nova parte do relatório: {report_file_path}")

    # Abre a primeira parte do relatório
    open_new_report_part()
    # --- Fim do Gerenciamento de Arquivos ---

    print(f"Iniciando escaneamento da pasta: {folder_path}")
    print(f"O relatório será salvo em múltiplas partes (max {MAX_REPORT_FILE_SIZE_BYTES / (1024*1024):.0f} MB por parte) na pasta do script.")
    print("-----------------------------------")
    print("")

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            
            base_name = os.path.basename(file_path)
            _, file_extension = os.path.splitext(file_name)
            file_extension = file_extension.lower()

            should_display_content = False
            content_to_write = "" # Variável para acumular o texto do bloco atual

            # --- Preparação do conteúdo para o relatório ---
            if file_extension in BINARY_EXTENSIONS:
                try:
                    file_size = os.path.getsize(file_path)
                    content_to_write = (
                        f"--- Caminho do arquivo (BINÁRIO): {file_path} ---\n"
                        f"[Conteúdo não exibido: Arquivo binário conhecido. Tamanho: {file_size / (1024*1024):.2f} MB]\n"
                        f"--- Fim do resumo de {base_name} ---\n\n"
                    )
                except OSError as e:
                    content_to_write = (
                        f"--- Caminho do arquivo (BINÁRIO): {file_path} ---\n"
                        f"[Conteúdo não exibido: Arquivo binário conhecido. Erro ao obter tamanho: {e}]\n"
                        f"--- Fim do resumo de {base_name} ---\n\n"
                    )
            elif base_name in TEXT_FILENAMES_NO_EXT or file_extension in TEXT_EXTENSIONS:
                should_display_content = True
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                        if not file_content.endswith('\n'):
                            file_content += '\n'
                        
                        content_to_write = (
                            f"--- Caminho do arquivo (TEXTO): {file_path} ---\n"
                            f"{file_content}"
                            f"--- Fim do conteúdo de {base_name} ---\n\n"
                        )
                except OSError as e:
                    content_to_write = (
                        f"--- Caminho do arquivo (TEXTO): {file_path} ---\n"
                        f"[ERRO AO ACESSAR ARQUIVO: {e}]\n"
                        f"--- Fim do conteúdo de {base_name} ---\n\n"
                    )
                except Exception as e:
                    content_to_write = (
                        f"--- Caminho do arquivo (TEXTO): {file_path} ---\n"
                        f"[ERRO AO LER CONTEÚDO: {e}]\n"
                        f"--- Fim do conteúdo de {base_name} ---\n\n"
                    )
            else:
                try:
                    file_size = os.path.getsize(file_path)
                    content_to_write = (
                        f"--- Caminho do arquivo (OUTRO TIPO): {file_path} ---\n"
                        f"[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. Tamanho: {file_size / (1024*1024):.2f} MB]\n"
                        f"--- Fim do resumo de {base_name} ---\n\n"
                    )
                except OSError as e:
                    content_to_write = (
                        f"--- Caminho do arquivo (OUTRO TIPO): {file_path} ---\n"
                        f"[Conteúdo não exibido: Tipo de arquivo não configurado para leitura. Erro ao obter tamanho: {e}]\n"
                        f"--- Fim do resumo de {base_name} ---\n\n"
                    )
            # --- Fim da preparação do conteúdo ---

            # --- Lógica de Quebra de Arquivo de Relatório (mais precisa) ---
            # Converte o conteúdo a ser escrito para bytes para verificar o tamanho
            # Assume UTF-8, o que é seguro para a maioria dos casos.
            content_bytes_length = len(content_to_write.encode('utf-8'))
            
            # Se o tamanho atual do arquivo MAIS o tamanho do próximo bloco de conteúdo
            # exceder o limite, abre uma nova parte.
            # O buffer adiciona uma margem para que a quebra ocorra um pouco antes do limite.
            if (report_file.tell() + content_bytes_length) > (MAX_REPORT_FILE_SIZE_BYTES - SIZE_CHECK_BUFFER_BYTES):
                current_part_number += 1
                open_new_report_part()
            # --- Fim da Lógica de Quebra ---

            # Escreve o conteúdo preparado no arquivo de relatório atual
            report_file.write(content_to_write)

    # Garante que a última parte do relatório seja fechada
    if report_file:
        report_file.write("-------------------------------------------------------------------\n")
        report_file.write("Escaneamento concluído.\n")
        report_file.close()
        print(f"Parte final do relatório concluída: {report_file.name}")

    print("Escaneamento concluído.")
    print(f"Relatório(s) salvo(s) com sucesso na pasta do script, com base em: {report_name_base}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python scan_folder_split_report.py <caminho_da_pasta>")
        print("Exemplo: python scan_folder_split_report.py /home/usuario/meus_documentos")
        sys.exit(1)

    target_folder = sys.argv[1]
    scan_folder_and_report_split(target_folder)