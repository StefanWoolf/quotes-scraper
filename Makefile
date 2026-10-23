IMAGE := quotes-scraper
# Дополнительные флаги docker build. В CI сюда передаётся кеш GitHub Actions
BUILD_FLAGS ?=

# Чтобы Git Bash на Windows не искажал пути в аргументах docker
export MSYS_NO_PATHCONV := 1

.PHONY: build run clean ci

build:
	docker build $(BUILD_FLAGS) -t $(IMAGE) .

run: build
	mkdir -p out
	docker run --rm -v "$(CURDIR)/out:/app/out" $(IMAGE)

clean:
	-docker rmi -f $(IMAGE)
	rm -rf out

ci: run
	test -s out/result.json
