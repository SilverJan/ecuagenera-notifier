DEST_SRC_DIR    ?= dist_src
DEST_DIR   		?= dist
VERSION			?= $(shell cat VERSION)

build: clean
	@echo "=====Build======"
	git pull
	./create_deb.sh

install: build
	@echo "=====Install======"
	sudo gdebi --non-interactive dist/ecuagenera_notifier_$(VERSION)_all.deb 

run_test:
	@echo "=====Test======"
	python3 -m pytest -v test/test_ecuagenera_notifier.py

clean_install: purge install

purge:
	@echo "=====Purge======"
	sudo apt purge -y ecuagenera-notifier || true

clean:
	@echo "=====Clean======"
	rm -rf $(DEST_DIR)
	rm -rf $(DEST_SRC_DIR)
