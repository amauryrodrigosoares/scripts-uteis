"""
Legado: use map_project.py. Este arquivo redireciona para manter compatibilidade.
"""
import sys

if __name__ == "__main__":
    print(
        "Aviso: map_project_structure.py está obsoleto. Prefira: python3 map_project.py <pasta>",
        file=sys.stderr,
    )
    from map_project import map_project_structure

    if len(sys.argv) < 2:
        print("Uso: python3 map_project.py <caminho_da_pasta_do_projeto>", file=sys.stderr)
        sys.exit(1)

    map_project_structure(sys.argv[1])
