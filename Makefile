.PHONY: clean virtualenv dist dist-upload

clean:
	find . -name '*.py[co]' -delete

virtualenv:
	virtualenv --prompt '|> python-terraform <| ' env
	env/bin/pip3 install -r requirements-dev.txt
	env/bin/python3 setup.py develop
	@echo
	@echo "VirtualENV Setup Complete. Now run: source /env/bin/activate"
	@echo "See https://virtualenv.readthedocs.io/en/latest/userguide/ for more details"
	@echo

dist: clean
	rm -rf dist/*
	python3 setup.py sdist
	python3 setup.py bdist_wheel

dist-upload:
	twine upload dist/*
