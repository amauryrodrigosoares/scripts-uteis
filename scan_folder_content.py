"""
Legado: use scan_folder.py. Este arquivo redireciona para manter compatibilidade.
"""
import sys

if __name__ == "__main__":
    print(
        "Aviso: scan_folder_content.py está obsoleto. Prefira: python3 scan_folder.py <pasta>",
        file=sys.stderr,
    )
    from scan_folder import scan_folder_and_report_split

    if len(sys.argv) < 2:
        print("Uso: python3 scan_folder.py <caminho_da_pasta>", file=sys.stderr)
        sys.exit(1)

    scan_folder_and_report_split(sys.argv[1])
