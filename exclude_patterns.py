"""
Regras compartilhadas para ignorar pastas sensíveis/lixo e arquivos com credenciais
nos relatórios gerados por map_project e scan_folder (antes: map_project_structure,
scan_folder_content).
"""
import os

EXCLUDED_DIR_NAMES = frozenset({
    # Controle de versão e IDEs
    '.git',
    '.github',
    '.cursor',
    '.idea',
    '.vscode',
    # Dependências
    'node_modules',
    'vendor',
    'venv',
    '.venv',
    # Builds e compilados
    'dist',
    'build',
    'out',
    '.turbo',
    '.next',
    'coverage',
    'bin',
    'pkg',
    # Caches
    '__pycache__',
    '.pytest_cache',
    '.eslintcache',
})

# Arquivos .env* que normalmente não contêm segredos reais (só modelos)
ALLOWED_ENV_STYLE_FILES = frozenset({
    '.env.example',
    '.env.sample',
    '.env.template',
    '.env.dist',
})

EXCLUDED_FILE_NAMES = frozenset({
    # Lockfiles grandes (irrelevantes para leitura de contexto)
    'package-lock.json',
    'yarn.lock',
    'composer.lock',
    'go.sum',
    # Credenciais/sensíveis
    '.env',
    '.env.local',
    '.env.development.local',
    '.env.production.local',
    '.env.test',
    '.npmrc',
    '.yarnrc',
    '.pypirc',
    '.netrc',
    'credentials.json',
    'serviceAccountKey.json',
    'id_rsa',
    'id_ecdsa',
    'id_ed25519',
    'id_dsa',
})

IGNORED_EXTENSIONS = frozenset({
    # Imagens e mídia
    '.png',
    '.jpg',
    '.jpeg',
    '.gif',
    '.svg',
    '.ico',
    '.mp4',
    '.mp3',
    # Binários e compactados
    '.zip',
    '.tar',
    '.gz',
    '.exe',
    '.dll',
    '.so',
    '.pyc',
    # Logs e bancos locais
    '.log',
    '.sqlite',
    '.sqlite3',
})

SENSITIVE_EXTENSIONS = frozenset({
    '.pem',
    '.key',
    '.p12',
    '.pfx',
    '.jks',
    '.keystore',
})


def prune_excluded_dirs(dirs):
    """Remove nomes de diretório excluídos da lista in-place (uso com os.walk)."""
    dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIR_NAMES)


def is_env_file(file_name: str) -> bool:
    """True se o nome for .env ou variante .env.*."""
    lowered_name = file_name.lower()
    return lowered_name == '.env' or lowered_name.startswith('.env.')


def should_exclude_file(file_name: str, include_env_files: bool = False) -> bool:
    """True se o arquivo não deve aparecer nos relatórios (nome apenas)."""
    lowered_name = file_name.lower()
    _, ext = os.path.splitext(lowered_name)

    if include_env_files and is_env_file(lowered_name):
        return False
    if lowered_name in ALLOWED_ENV_STYLE_FILES:
        return False
    if lowered_name in EXCLUDED_FILE_NAMES:
        return True
    if lowered_name.startswith('.env.') and lowered_name not in ALLOWED_ENV_STYLE_FILES:
        return True
    if ext in IGNORED_EXTENSIONS:
        return True
    if ext in SENSITIVE_EXTENSIONS:
        return True
    if lowered_name.endswith('.keystore'):
        return True
    return False
