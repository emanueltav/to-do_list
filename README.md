1.  **Crie um ambiente virtual:**
    python -m venv .venv

2.  **Ative o ambiente virtual:**
    .venv\Scripts\activate
    (Para outros sistemas operacionais (Linux/macOS), o comando é `source .venv/bin/activate)

3.  **Instale as dependências:**
    pip install flask flask-login flask-wtf flask-sqlalchemy

4.  **Gere o arquivo `requirements.txt`:**
    pip freeze > requirements.txt
