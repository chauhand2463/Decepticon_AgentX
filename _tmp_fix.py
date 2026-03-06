import os
import re

def remove_python_comments(source):
    source = re.sub(r'#.*$', '', source, flags=re.MULTILINE)
    source = re.sub(r'"{3}[\s\S]*?"{3}', '', source)
    source = re.sub(r"'{3}[\s\S]*?'{3}", '', source)
    return source

def remove_general_comments(source, extension):
    if extension in ['.js', '.css', '.ts', '.tsx', '.jsx']:
        source = re.sub(r'/\*[\s\S]*?\*/', '', source)
        source = re.sub(r'//.*$', '', source, flags=re.MULTILINE)
    elif extension in ['.html', '.xml']:
        source = re.sub(r'<!--[\s\S]*?-->', '', source)
    elif extension in ['.yaml', '.toml', '.txt', 'Dockerfile', '.ps1', '.sh', '.env', '.gitignore']:
        source = re.sub(r'#.*$', '', source, flags=re.MULTILINE)
    return source

def process_file(file_path):
    ext = os.path.splitext(file_path)[1]
    filename = os.path.basename(file_path)
    if not ext and filename in ['Dockerfile', 'LICENSE']:
        ext = filename

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if ext == '.py':
            new_content = remove_python_comments(content)
        else:
            new_content = remove_general_comments(content, ext)

        new_content = "\n".join([line.rstrip() for line in new_content.splitlines()])
        new_content = re.sub(r'\n{3,}', '\n\n', new_content)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
    except Exception as e:
        print(f"Failed to process {file_path}: {e}")

def replace_branding(file_path):
    replacements = {
        'DECEPTICON': 'DECEPTICON',
        'PurpleAILAB': 'PurpleAILAB',
        'chauhand2463': 'chauhand2463',
        'decepticon.cyber': 'decepticon.cyber',
        'https://github.com/PurpleAILAB/DECEPTICON': 'https://github.com/chauhand2463/Decepticon'
    }
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        new_content = content
        for old, new in replacements.items():
            new_content = new_content.replace(old, new)
            new_content = new_content.replace(old.lower(), new.lower())

        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
    except:
        pass
    return False

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    exclude_dirs = {'.git', '.venv', '__pycache__', 'node_modules', '.streamlit', 'assets', 'data'}
    exclude_files = {'_tmp_fix.py', 'uv.lock', 'LICENSE', 'README_KO.md', 'README.md', 'pyproject.toml'}

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        for file in files:
            file_path = os.path.join(root, file)

            replace_branding(file_path)

            if file not in exclude_files:
                print(f"Processing {file_path}")
                process_file(file_path)

if __name__ == "__main__":
    main()
