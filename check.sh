#! usr/bin/bash
echo -e "\033[1;34mRunning tests and style checks...\033[0m"
echo -e "\033[1;33mRequirements:\033[0m"
echo -e "  - \033[0;32mpytest\033[0m, \033[0;32mflake8\033[0m, and \033[0;32mmypy\033[0m must be installed."
echo -e "  - The virtual environment should be \033[1;35mactivated\033[0m."
echo -e "  - The virtual environment is expected to be located in a directory named \033[1;35m.venv\033[0m at the project's root."

# Your script continues here...

# Find all Python files excluding the .venv directory and save to a temporary file
find . -type f -name "*.py" ! -path "./.venv/*" -print0 > python_files.tmp

# Run pytest on the found files
xargs -0 pytest < python_files.tmp

# Run flake8 on the found files
xargs -0 flake8 < python_files.tmp

# Run mypy on the found files
# Note: mypy might not support reading from stdin like this, so we convert the null-separated strings to newline-separated.
xargs -0 -a python_files.tmp mypy

# Clean up the temporary file
rm -f python_files.tmp