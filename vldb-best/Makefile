SOURCES=example1.tex example2.tex example3.tex implementation.tex	\
	main.tex recursion.tex relational.tex conclusions.tex		\
	extensions.tex intro.tex nested.tex related.tex	\
	streams.tex incview.pdf indexed.pdf tools.pdf view.pdf \
	experiments.tex graph/*.pdf

TARGET = main.pdf

$(TARGET): $(SOURCES) main.bib
	pdflatex main
	bibtex main
	pdflatex main

clean:
	rm -f *.aux *.log *.dvi *.blg *.out *.bbl *.xmpi


