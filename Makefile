install:
	cp notes2web/usr/local/bin
	mkdir -p /opt/notes2web
	cp -r templates /opt/notes2web
	cp styles.css /opt/notes2web

clean:
	rm -rf /usr/local/bin/notes2web/opt/notes2web
