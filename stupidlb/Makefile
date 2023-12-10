#!/usr/bin/make -f

VALUES = --values dev-values.yaml

.PHONY: diff
diff:
	helm diff upgrade --install --context 3 --values values.yaml $(VALUES) stupidlb .

.PHONY: upgrade
upgrade: diff
	helm upgrade --install --values values.yaml $(VALUES) stupidlb .
