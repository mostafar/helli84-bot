

virtualenv:
		virtualenv --python /usr/bin/python3.4 ./venv


install: virtualenv
		. ./venv/bin/activate; pip install -r requirements.txt
