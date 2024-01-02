install:
	cp  gronk_add_uuid.py /usr/local/bin
	sed "s/GRONK_COMMIT = \"dev\"/GRONK_COMMIT = \"$$(git rev-parse --short HEAD)\"/" gronk.py > /usr/local/bin/gronk.py
	chmod +x /usr/local/bin/gronk.py
	chmod +x /usr/local/bin/gronk_add_uuid.py
	mkdir -p /opt/gronk
	cp -r templates js css /opt/gronk
	pip3 install -r requirements.txt

uninstall:
	rm -rf /usr/local/bin/gronk.py /usr/local/bin/gronk_add_uuid.py /opt/gronk
