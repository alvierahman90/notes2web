install:
	cp  n2w_add_uuid.py /usr/local/bin
	sed "s/N2W_COMMIT = \"\"/N2W_COMMIT = \"$$(git rev-parse --short HEAD)\"/" notes2web.py > /usr/local/bin/notes2web.py
	pip3 install -r requirements.txt
	mkdir -p /opt/notes2web
	cp -r templates /opt/notes2web
	cp styles.css /opt/notes2web
	cp fuse.js /opt/notes2web
	cp search.js /opt/notes2web
	cp toc_search.js /opt/notes2web
	cp permalink.js /opt/notes2web

uninstall:
	rm -rf /usr/local/bin/notes2web.py /usr/local/bin/n2w_add_uuid.py /opt/notes2web
