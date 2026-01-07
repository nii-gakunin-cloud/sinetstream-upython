PYTHON3=python3
CONFIG=src/sinetstream_config.json

all:: venv/bin/sinetstream_cli
	cp $(CONFIG) venv/.sinetstream_config.yml
	cd venv && bin/sinetstream_cli read --text

venv/bin/sinetstream_cli: venv
	venv/bin/python -m pip install sinetstream_cli
	touch $@
venv:
	$(PYTHON3) -m venv venv

clean::
distclean:: clean
	-rm -rf venv
