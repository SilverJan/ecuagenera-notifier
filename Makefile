DEST_SRC_DIR    ?= dist_src
DEST_DIR   		?= dist
VERSION			?= $(shell cat VERSION)
SSH_USER		?= pi
SSH_HOST		?= 192.168.1.94

build: clean
	@echo "=====Build======"
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

# Operation commands

deploy: build
	@echo "=====Deploy latest package on SSH server======"
	scp dist/ecuagenera-notifier_$(VERSION)_all.deb $(SSH_USER)@$(SSH_HOST):/tmp/
	ssh -t $(SSH_USER)@$(SSH_HOST) "cd /home/$(SSH_USER)/dev/ecuagenera-notifier; make purge; sudo gdebi --non-interactive /tmp/ecuagenera-notifier_$(VERSION)_all.deb"

copy_config:
	@echo "=====Copy config from local to SSH server======"
	scp src/opt/ecuagenera-notifier/config.yml $(SSH_USER)@$(SSH_HOST):/opt/ecuagenera-notifier/config.yml

check_status:
	@echo "=====Check system status on SSH server======"
	ssh -t $(SSH_USER)@$(SSH_HOST) "systemctl status --no-pager ecuagenera-notifier.service;"

ssh:
	@echo "=====Connect to SSH server======"
	ssh $(SSH_USER)@$(SSH_HOST) 