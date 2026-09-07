.PHONY: lint test hooks venv figures
lint:    ## 结构校验
	python3 tools/lint.py
test:    ## 工具单测
	python3 -m unittest discover -s tools -p 'test_*.py' -v
hooks:   ## 安装 git 钩子（clone 后跑一次）
	sh tools/install-hooks.sh
venv:    ## 出图环境
	python3 -m venv .venv && .venv/bin/pip install -q -r tools/figures/requirements.txt
figures: ## 重出全部图
	for f in tools/figures/[a-z]*.py; do .venv/bin/python "$$f" || exit 1; done
