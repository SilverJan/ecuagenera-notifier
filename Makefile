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
	sudo gdebi --non-interactive dist/ecuagenera_bot_$(VERSION)_all.deb 

run_test:
	@echo "=====Test======"
	python3 -m pytest -v test/test_ecuagenera_bot.py

clean_install: purge install

purge:
	@echo "=====Purge======"
	sudo apt purge -y ecuagenera-bot || true

clean:
	@echo "=====Clean======"
	rm -rf $(DEST_DIR)
	rm -rf $(DEST_SRC_DIR)

# Operation commands

deploy: build
	@echo "=====Deploy latest package on SSH server======"
	scp dist/ecuagenera-bot_$(VERSION)_all.deb $(SSH_USER)@$(SSH_HOST):/tmp/
	ssh -t $(SSH_USER)@$(SSH_HOST) "sudo apt purge -y ecuagenera-bot; sudo gdebi --non-interactive /tmp/ecuagenera-bot_$(VERSION)_all.deb"

check_status:
	@echo "=====Check system status on SSH server======"
	ssh -t $(SSH_USER)@$(SSH_HOST) "systemctl status --no-pager ecuagenera-bot.service ecuagenera-registration-monitor.service ecuagenera-telegram-bot.service; PYTHONPATH=/opt/ecuagenera-bot python3 -m ecua_helpers.get_telegram_linked_accounts"

ssh:
	@echo "=====Connect to SSH server======"
	ssh $(SSH_USER)@$(SSH_HOST)
