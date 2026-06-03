.PHONY: all install run test lint clean

all: install run

install:
	pip3 install -e .

install-dev:
	pip3 install -e ".[dev]"

run:
	python33 main.py

run-debug:
	FLASK_DEBUG=1 python33 main.py

test:
	pytest tests/ -v

lint:
	flake8 core/ api/ --max-line-length=120

format:
	black core/ api/

clean:
	rm -rf __pycache__
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf logs/*.log

init-db:
	python33 -c "from core import db; print('Database initialized')"

backup-db:
	python33 -c "from core import db; db.backup()"

health-check:
	python33 -c "from core import system; print(system.get_health_report())"
