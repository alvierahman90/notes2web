install:
	cp notes2web.py /usr/local/bin
	pip install -r requirements.txt
	mkdir -p /opt/notes2web
	cp -r templates /opt/notes2web
	cp styles.css /opt/notes2web
	cp fuse.js /opt/notes2web
	cp search.js /opt/notes2web

uninstall:
	rm -rf /usr/local/bin/notes2web.py /opt/notes2web
