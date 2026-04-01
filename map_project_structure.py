import os
import sys
import datetime

from exclude_patterns import prune_excluded_dirs, should_exclude_file

# --- Constantes de Configuração ---
# Estes são os tipos de arquivos que queremos categorizar claramente
# Você pode expandir ou modificar estas listas conforme a necessidade do seu projeto
PROGRAMMING_FILES = ('.py', '.js', '.jsx', '.ts', '.tsx', '.php', '.java', '.c', '.cpp', '.h', '.hpp',
                     '.rb', '.go', '.swift', '.kt', '.vue', '.html', '.css', '.scss', '.less', '.sql',
                     '.sh', '.bat', '.ps1', '.pl', '.lua', '.rs')

CONFIG_FILES = ('.json', '.xml', '.yaml', '.yml', '.ini', '.conf', '.toml', '.env',
                'package.json', 'composer.json', 'Gemfile', 'Rakefile', 'Makefile',
                '.gitignore', '.gitattributes', '.editorconfig', 'Dockerfile', 'webpack.config.js')

DOCUMENT_FILES = ('.md', '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
                  '.odt', '.ods', '.odp', '.csv', '.tsv', 'LICENSE', 'README', 'CHANGELOG')

IMAGE_FILES = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.webp')

ARCHIVE_FILES = ('.zip', '.gz', '.tar', '.rar', '.7z', '.bz2', '.tgz')

# Adicione mais categorias se necessário, ou deixe como 'OTHER'
# --- Fim das Constantes ---

def get_file_category(file_name):
    """Categoriza um arquivo baseado em sua extensão ou nome."""
    _, ext = os.path.splitext(file_name)
    ext = ext.lower()

    if file_name.lower() in [f.lower() for f in CONFIG_FILES]: # Verifica nome completo para config
        return "Configuração"
    elif ext in PROGRAMMING_FILES:
        return "Código-Fonte"
    elif ext in CONFIG_FILES: # Verifica extensão para config
        return "Configuração"
    elif ext in DOCUMENT_FILES:
        return "Documento"
    elif ext in IMAGE_FILES:
        return "Imagem"
    elif ext in ARCHIVE_FILES:
        return "Arquivo Comprimido"
    # Você pode adicionar mais categorias aqui
    else:
        # Tenta categorizar arquivos sem extensão (como .env)
        if '.' not in file_name and file_name.lower() in [f.lower() for f in CONFIG_FILES]:
            return "Configuração"
        return "Outro"


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
    return caminho_saida


def map_project_structure(folder_path):
    """
    Mapeia a estrutura de pastas e arquivos de um projeto, listando nomes e tipos.
    Gera um relatório formatado para fácil compreensão por um modelo de linguagem.
    """
    if not os.path.isdir(folder_path):
        print(f"Erro: O caminho '{folder_path}' não é um diretório válido.")
        return

    # --- Definição da Pasta de Saída e Nome do Relatório ---
    output_dir = preparar_pasta_de_saida(folder_path)
    report_filepath = os.path.join(output_dir, "estrutura_do_projeto.txt")
    # --- Fim da Definição ---

    print(f"Iniciando mapeamento da estrutura do projeto em: {folder_path}")
    print(f"Os arquivos gerados serão salvos em: {output_dir}")
    print(f"O relatório será salvo em: {report_filepath}")
    print("-----------------------------------")
    print("")

    with open(report_filepath, 'w', encoding='utf-8') as report_file:
        report_file.write(f"--- Mapeamento da Estrutura do Projeto: {folder_path} ---\n")
        report_file.write(f"Gerado em: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        report_file.write("-------------------------------------------------------------------\n\n")
        report_file.write("Objetivo: Entender a organização do projeto pelo nome e tipo de arquivos.\n")
        report_file.write("Símbolos: [D] = Diretório, [F] = Arquivo\n")
        report_file.write("-------------------------------------------------------------------\n\n")

        # Percorre a árvore de diretórios (ignora .git, IDEs, node_modules, etc.)
        for root, dirs, files in os.walk(folder_path):
            prune_excluded_dirs(dirs)
            visible_files = [f for f in files if not should_exclude_file(f, include_env_files=True)]

            # Calcula o nível de indentação para a formatação da árvore
            # +1 para a própria pasta base para que não comece sem indentação
            level = root.replace(folder_path, '').count(os.sep)
            indent = '    ' * (level) # 4 espaços por nível

            # Escreve o diretório atual
            report_file.write(f"{indent}[D] {os.path.basename(root)}/\n")

            # Lista arquivos neste diretório (omitindo sensíveis)
            for file_name in sorted(visible_files):
                file_category = get_file_category(file_name)
                report_file.write(f"{indent}    [F] {file_name} (Tipo: {file_category})\n")

            # Adiciona uma linha em branco para melhor legibilidade entre diretórios grandes
            if visible_files or dirs:
                report_file.write("\n")

        report_file.write("-------------------------------------------------------------------\n")
        report_file.write("Mapeamento da estrutura concluído.\n")

    print("Mapeamento concluído.")
    print(f"Relatório da estrutura salvo com sucesso em: {report_filepath}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python map_project_structure.py <caminho_da_pasta_do_projeto>")
        print("Exemplo: python map_project_structure.py /home/usuario/meu_projeto_web")
        sys.exit(1)

    target_folder = sys.argv[1]
    map_project_structure(target_folder)
