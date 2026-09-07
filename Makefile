.PHONY: lint test hooks
lint:  ## 结构校验
	python3 tools/lint.py
test:  ## 工具单测
	python3 -m unittest discover -s tools -p 'test_*.py' -v
hooks: ## 安装 git 钩子（clone 后跑一次）
	sh tools/install-hooks.sh
