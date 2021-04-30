install:
	cp gen_notes.sh /usr/local/bin
	mkdir -p /opt/gen_notes
	cp -r templates /opt/gen_notes
	cp styles.css /opt/gen_notes

clean:
	rm -rf /usr/local/bin/gen_notes.sh /opt/gen_notes
