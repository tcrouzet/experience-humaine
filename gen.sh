#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
python_bin="python3"
if [[ -x "$script_dir/venv/bin/python" ]]; then
  python_bin="$script_dir/venv/bin/python"
fi
"$python_bin" "$script_dir/script/generate.py"
"$python_bin" "$script_dir/script/generate_social.py"
"$python_bin" "$script_dir/script/generate_pdf.py"
