#!/usr/bin/make -f

export KUBECTL_CONTEXT=home
export KUBECTL_NAMESPACE=kj

.PHONY: run
run : pylint
	# . bin/activate; kopf run --all-namespaces --dev stupidlb.py
	. bin/activate; kopf run --namespace kj --dev stupidlb.py

.PHONY: pylint
pylint :
	. bin/activate; pylint stupidlb.py
