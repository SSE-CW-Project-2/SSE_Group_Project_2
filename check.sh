#!/usr/bin/env bash

echo -e "\033[1;33mRequirements:\033[0m"
echo -e "  - The script must be run from the project's \033[0;32mroot\033[0m directory."
echo -e "  - \033[0;32mpytest\033[0m, \033[0;32mflake8\033[0m, and \033[0;32mmypy\033[0m must be installed."
echo -e "  - The virtual environment should be \033[1;35mactivated\033[0m."
echo -e "  - The virtual environment is expected to be located in a directory named \033[1;35m.venv\033[0m at the project's root."
echo -e "\033[1;34mRunning style checks...\033[0m"

find . -type f -name "*.py" ! -path "./.venv/*" -print0 > python_files.tmp
xargs -0 flake8 < python_files.tmp --extend-ignore E203  --extend-ignore E722 --max-line-length 120
xargs -0 -a python_files.tmp mypy --ignore-missing-imports
rm -f python_files.tmp

# TESTING
echo -e "\033[1;34mRunning tests...\033[0m"
cd api
flask run &
FLASK_PID=$!
find tests -type f -name "*.py" -exec pytest {} +
kill $FLASK_PID

cd ..
