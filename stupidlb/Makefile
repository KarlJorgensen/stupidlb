#!/usr/bin/make -f

SETS = --set image.pullPolicy=Always --set CIDRs=192.168.0.224/28

.PHONY: diff
diff:
	helm diff upgrade --install --context 3 --values values.yaml $(SETS) stupidlb .

.PHONY: upgrade
upgrade: diff
	helm upgrade --install --values values.yaml $(SETS) stupidlb .
