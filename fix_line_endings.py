#!/usr/bin/env python3
"""Script para corrigir line endings CRLF para LF em arquivos shell"""

import os
from pathlib import Path

def fix_line_endings(file_path):
    """Converte CRLF para LF"""
    with open(file_path, 'rb') as f:
        content = f.read()
    
    # Substituir CRLF por LF
    content = content.replace(b'\r\n', b'\n')
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    print(f"OK Corrigido: {file_path}")

def main():
    """Corrige todos os arquivos .sh no diretório docker/"""
    docker_dir = Path(__file__).parent / 'docker'
    
    for sh_file in docker_dir.glob('*.sh'):
        fix_line_endings(sh_file)
    
    print("\nTodos os arquivos .sh foram corrigidos!")

if __name__ == '__main__':
    main()

