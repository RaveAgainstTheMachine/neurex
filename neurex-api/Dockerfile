FROM python:3.12-slim

WORKDIR /app

# System deps for tree-sitter, ptyprocess
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ git curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-compile tree-sitter grammars
RUN python -c "import tree_sitter_languages; print('tree-sitter OK')"

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
