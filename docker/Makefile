#!/usr/bin/make -f

SUFFIX=
VERSION=$(shell cat ../version.txt)
REPO=karljorgensen/stupidlb

IMAGE=$(REPO):$(VERSION)$(SUFFIX)

# Dummy CIDRs for testing
export CIDRS = 192.168.0.224/28,192.168.50.1

.PHONY: image
image: pylint
	docker build -t $(IMAGE) .

.PHONY: push
push: image
	docker push -q $(IMAGE)

# The namespace indicated by the current kubectl context
KUBECTL_NAMESPACE = $(shell kubectl config view --minify -o jsonpath='{..namespace}' )

.PHONY: run
run : pylint test-setup
	. ../bin/activate; kopf run --namespace $(KUBECTL_NAMESPACE) --dev stupidlb.py

.PHONY: test-setup
test-setup: clean-service
	kubectl apply -f test-services.yaml

.PHONY: clean clean-service
clean clean-service:
	kubectl delete service -l stupidlb-test

.PHONY: pylint
pylint :
	. ../bin/activate; pylint stupidlb.py
