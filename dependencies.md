# Walk Prague — Dependencies

## Runtime
- **Python 3** (developed and tested on Python 3.11; any 3.10+ works).
- **SQLite** — nothing to install; it is part of Python's standard library
  (`sqlite3`), and the database file ships with the project.

## Python packages
All third-party packages are listed in **`requirements.txt`**:

| Package | Version | Purpose |
|---------|---------|---------|
| Flask | 3.0.3 | web framework — routing, templating (Jinja2), sessions |
| Werkzeug | 3.0.3 | WSGI utilities and secure password hashing (Flask dependency) |
| Flask-Login | 0.6.3 | authentication / login-session management |

## Run the following line below in the terminal to install the dependencies needed 

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```



