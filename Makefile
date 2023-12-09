#!/usr/bin/make -f

.PHONY: all
all : docker-push helm-upgrade rollout-restart

.PHONY: docker-push
docker-push:
	$(MAKE) -C docker push

.PHONY: helm-upgrade
helm-upgrade:
	$(MAKE) -C stupidlb upgrade

.PHONY: rollout-restart
rollout-restart:
	kubectl rollout restart deploy stupidlb
