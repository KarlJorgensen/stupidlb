#!/usr/bin/make -f

export KUBECTL_CONTEXT=home
export KUBECTL_NAMESPACE=kj

.PHONY: run
run : pylint test-setup
	. bin/activate; kopf run --namespace $(KUBECTL_NAMESPACE) --dev stupidlb.py

.PHONY: pylint
pylint :
	. bin/activate; pylint stupidlb.py

.PHONY: test-setup
test-setup: clean-service
	kubectl --namespace $(KUBECTL_NAMESPACE) apply -f test-services.yaml

.PHONY: clean clean-service
clean clean-service:
	kubectl --namespace $(KUBECTL_NAMESPACE) delete service -l stupidlb-test
