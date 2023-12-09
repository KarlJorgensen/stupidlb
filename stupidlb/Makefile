#!/usr/bin/make -f

SETS = --set image.pullPolicy=Always
.PHONY: diff
diff:
	helm diff upgrade --install --context 3 --values values.yaml $(SETS) stupidlb .

.PHONY: upgrade
upgrade: diff
	helm upgrade --install --values values.yaml $(SETS) stupidlb .
