# Makefile for RISC-V ISA Manuals
#
# This work is licensed under the Creative Commons Attribution-ShareAlike 4.0
# International License. To view a copy of this license, visit
# http://creativecommons.org/licenses/by-sa/4.0/ or send a letter to
# Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
#
# SPDX-License-Identifier: CC-BY-SA-4.0
#
# Description:
# 
# This Makefile is designed to automate the process of building and packaging 
# the documentation for RISC-V ISA Manuals. It supports multiple build targets 
# for generating documentation in various formats (PDF, HTML).

# Build Targets
TARGETS := debug debug-HTML

# Declare phony targets
.PHONY: all $(TARGETS) clean

# Default target builds all
all: $(TARGETS)

# Build with preinstalled docker container; first install it with:
#   docker pull riscvintl/riscv-docs-base-container-image:latest
docker:
	cd .. && docker run -it -v .:/build riscvintl/riscv-docs-base-container-image:latest /bin/sh -c 'cd ./build; make $(MAKEFLAGS)'

# Asciidoctor options
ASCIIDOCTOR_OPTS := -a compress \
                    --attribute=mathematical-format=svg \
                    --failure-level=ERROR \
                    --require=asciidoctor-diagram \
                    --require=asciidoctor-mathematical \
                    --trace
#                    --require=asciidoctor-bibtex \
# Source directory
SRCDIR := ../

# Temporary files to clean up for LaTeX build
JUNK := *.pdf *.aux *.log *.bbl *.blg *.toc *.out *.fdb_latexmk *.fls *.synctex.gz

# RISC-V Debug spec PDF build
debug: riscv-debug-spec.pdf

riscv-debug-spec.pdf: $(SRCDIR)/riscv-debug-header.adoc $(SRCDIR)/*.adoc
	@echo "Building Debug Specification"
	rm -f $@.tmp
	asciidoctor-pdf $(ASCIIDOCTOR_OPTS) --out-file=$@.tmp $<
	mv $@.tmp $@

# RISC-C Debug spec HTML build
debug-html: riscv-debug-spec.html

riscv-debug-spec.html: $(SRCDIR)/riscv-debug-header.adoc
	@echo "Building Debug Specification HTML"
	asciidoctor $(ASCIIDOCTOR_OPTS) --out-file=$@ $<

clean:
	@if [ -f riscv-debug-spec.pdf ]; then \
		echo "Removing riscv-debug-spec.pdf"; \
		rm -f riscv-debug-spec.pdf; \
	fi
	@if [ -f riscv-debug-spec.html ]; then \
		echo "Removing riscv-debug-spec.html"; \
		rm -f riscv-debug-spec.html; \
	fi