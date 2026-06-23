pip install --upgrade pip
pip install --only-binary=:all: pydantic-core 2>&1 || true
pip install -r requirements.txt
