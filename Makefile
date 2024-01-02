install:
	cp  n2w_add_uuid.py /usr/local/bin
	sed "s/N2W_COMMIT = \"\"/N2W_COMMIT = \"$$(git rev-parse --short HEAD)\"/" notes2web.py > /usr/local/bin/notes2web.py
	mkdir -p /opt/notes2web
	cp -r templates js css /opt/notes2web
	pip3 install -r requirements.txt

uninstall:
	rm -rf /usr/local/bin/notes2web.py /usr/local/bin/n2w_add_uuid.py /opt/notes2web
