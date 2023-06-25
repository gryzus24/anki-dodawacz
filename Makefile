PROG=ankidodawacz
PREFIX=/usr/local
BINDIR=${PREFIX}/bin
PROGDIR=${PREFIX}/share/${PROG}

install:
	mkdir -p ${PROGDIR}
	mkdir -p ${BINDIR}
	cp -r lib/bs4 lib/lxml lib/urllib3 src ${PROGDIR}
	cp config.json gryzus-std.json ${PROG}.py ${PROGDIR}
	chmod 755 ${PROGDIR}/${PROG}.py
	python3 -m compileall -q ${PROGDIR}
	ln -sf ${PROGDIR}/${PROG}.py ${BINDIR}/${PROG}

uninstall:
	rm -f ${BINDIR}/${PROG}
	rm -rf ${PROGDIR}

clean:
	find src -type d -name __pycache__ -exec rm -r {} +

.PHONY: install uninstall clean
