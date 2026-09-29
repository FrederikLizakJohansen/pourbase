.PHONY: all assets clean

all: assets manuscript.pdf

assets:
	python scripts/generate_paper_assets.py

manuscript.pdf: manuscript.tex generated/dataset-statistics.tex generated/references.tex
	lualatex -interaction=nonstopmode -halt-on-error manuscript.tex
	lualatex -interaction=nonstopmode -halt-on-error manuscript.tex

clean:
	rm -f manuscript.aux manuscript.log manuscript.out manuscript.pdf
