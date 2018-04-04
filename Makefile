.PHONY: pypi, test

pypi:
	rm dist/*
	python setup.py sdist
	twine upload --config-file=.pypirc dist/*

test:
	PYTHONPATH=.:testing:testing/tests:testing/tests/py2-dj14_testproject \
	DJANGO_SETTINGS_MODULE=py2-dj14_testproject.settings \
	DJANGO_CONCURRENT_TESTS_TIMEOUT=10 \
	py.test -v -s -pdb testing/tests
