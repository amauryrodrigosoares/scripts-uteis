"""
Legado: use scan_folder.py. Este arquivo redireciona para manter compatibilidade.
"""
import sys

if __name__ == "__main__":
    print(
        "Aviso: scan_folder_content.py está obsoleto. Prefira: python3 scan_folder.py <pasta>",
        file=sys.stderr,
    )
    from scan_folder import main

    main()
