BASE=vpnupdate
TAG=$(BASE):latest

build:
	docker build -t $(TAG)

run:
	docker run --rm -it $(TAG)