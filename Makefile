CC=$(RISCV)/bin/riscv64-unknown-elf-gcc

NAME=riscv-debug-spec

REGISTERS_TEX = jtag_registers.tex
REGISTERS_TEX += core_registers.tex
REGISTERS_TEX += hwbp_registers.tex
REGISTERS_TEX += dm1_registers.tex
REGISTERS_TEX += dm2_registers.tex
REGISTERS_TEX += trace_registers.tex
REGISTERS_TEX += sample_registers.tex

FIGURES = *.eps

riscv-debug-spec.pdf: $(NAME).tex $(REGISTERS_TEX) debug_rom.S $(FIGURES)
	pdflatex -shell-escape $< && pdflatex -shell-escape $<

%.eps: %.dot
	dot -Teps $< -o $@

%.tex: %.xml registers.py
	./registers.py --custom --definitions $@.inc --cheader $@.h $< > $@

%.o:	%.S
	$(CC) -c $<

# Remove 128-bit instructions since our assembler doesn't like them.
%_no128.S:	%.S
	sed "s/\([sl]q\)/nop\#\1/" < $< > $@

debug_rom:	debug_rom_no128.o main.o
	$(CC) -o $@ $^ -Os

debug_ram:	debug_ram.o main.o
	$(CC) -o $@ $^

hello:	hello.c
	$(CC) -o $@ $^ -Os

hello.s:	hello.c
	$(CC) -o $@ $^ -S -Os

clean:
	rm -f $(NAME).pdf $(NAME).aux $(NAME).toc $(NAME).log $(REGISTERS_TEX) \
	    $(REGISTERS_TEX:=.inc) *.o *_no128.S *.h $(NAME).lof $(NAME).lot $(NAME).out \
	    $(NAME).hst $(NAME).pyg
