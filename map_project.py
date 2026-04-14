import datetime
import os
import sys
from pathlib import Path

from exclude_patterns import prune_excluded_dirs, should_exclude_file


def _safe_tree_path(s: str) -> str:
    """
    Normaliza caminho para texto seguro em ingestão tipo Notebook LM:
    sem quebras de linha, crases (cercas Markdown) nem caracteres de controle.
    """
    out = []
    for ch in s:
        if ch in "\n\r":
            out.append("_")
        elif ch == "`":
            out.append("'")
        elif ch == "\t":
            out.append(" ")
        elif ord(ch) < 32:
            out.append("_")
        else:
            out.append(ch)
    return "".join(out)


def preparar_pasta_de_saida(caminho_projeto):
    """
    Cria uma pasta organizada para salvar os relatórios da execução atual.
    Retorna o caminho absoluto dessa nova pasta.
    """
    nome_projeto = os.path.basename(os.path.normpath(caminho_projeto))
    if not nome_projeto:
        nome_projeto = "projeto_desconhecido"

    nome_projeto = "".join(c if c.isalnum() or c in ["-", "_"] else "_" for c in nome_projeto)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    nome_pasta_execucao = f"relatorio_{nome_projeto}_{timestamp}"

    diretorio_do_script = os.path.dirname(os.path.abspath(__file__))
    caminho_saida = os.path.join(diretorio_do_script, "relatorios", nome_pasta_execucao)
    os.makedirs(caminho_saida, exist_ok=True)
    return caminho_saida


def map_project_structure(folder_path):
    """
    Mapeia pastas e arquivos (caminhos relativos em POSIX).
    Gera só `estrutura_notebook_lm.md`: corpo em texto puro (linhas D/F), sem cercas nem front matter — mínimo de tokens; extensão .md para o Notebook LM e editores.
    """
    if not os.path.isdir(folder_path):
        print(f"Erro: O caminho '{folder_path}' não é um diretório válido.")
        return

    output_dir = preparar_pasta_de_saida(folder_path)
    report_filepath = os.path.join(output_dir, "estrutura_notebook_lm.md")

    folder_root = os.path.abspath(folder_path)

    print(f"Iniciando mapeamento da estrutura do projeto em: {folder_path}")
    print(f"Os arquivos gerados serão salvos em: {output_dir}")
    print(f"O relatório será salvo em: {report_filepath}")
    print("-----------------------------------")
    print("")

    lines = []
    for root, dirs, files in os.walk(folder_root):
        prune_excluded_dirs(dirs)
        visible_files = [
            f for f in files
            if not should_exclude_file(f, include_env_files=True, for_content_scan=False)
        ]

        rel = os.path.relpath(root, folder_root)
        rel_posix = Path(rel).as_posix()
        if rel_posix == ".":
            dir_display = "./"
        else:
            dir_display = rel_posix + "/"
        lines.append("D " + _safe_tree_path(dir_display))

        for file_name in sorted(visible_files):
            if rel_posix == ".":
                file_rel = file_name
            else:
                file_rel = f"{rel_posix}/{file_name}"
            lines.append("F " + _safe_tree_path(file_rel))

    body = "\n".join(lines)
    if body:
        body += "\n"

    with open(report_filepath, "w", encoding="utf-8", newline="\n") as report_file:
        report_file.write(body)

    print("Mapeamento concluído.")
    print(f"Relatório da estrutura salvo com sucesso em: {report_filepath}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 map_project.py <caminho_da_pasta_do_projeto>")
        print("Exemplo: python3 map_project.py /home/usuario/meu_projeto_web")
        sys.exit(1)

    target_folder = sys.argv[1]
    map_project_structure(target_folder)
