RISC-V Debug Specification
==========================

You may be looking for one of the following pre-built PDFs:
* [Latest release candidate](https://github.com/riscv/riscv-debug-spec/releases)
* [Latest release](https://github.com/riscv/riscv-debug-spec/blob/release/riscv-debug-release.pdf)
  (This is outdated at this point, and only of historical interest.)

Build Instructions
------------------

```bash
# Install docker and python3-sympy, if not installed already.

# Pull the latest RISC-V Docs container image:
docker pull riscvintl/riscv-docs-base-container-image:latest

git clone https://github.com/riscv/riscv-debug-spec.git
cd riscv-debug-spec

# Optionally, check out a specific revision:
# git checkout <rev>

git submodule update --init --recursive

cd build
make
```

There are two other interesting make targets:

1. `make debug_defines` creates a C header and implementation files containing
   constants for addresses and fields of all the registers and abstract
   commands, as well as function and structures used to decode register values.
   An implementation of such decoder can be seen in `debug_reg_printer.c/h`.
2. `make chisel` creates scala files for DM registers and abstract commands
   with the same information.

Contributing
------------------

There are various ways to contribute to this spec. You can use a combination of them to get your idea across.
Please note that pull requests will only be reviewed/accepted from RISC-V Foundation members.

1. Make a PR. This is the best way to deal with minor typos and edits.
2. File an issue with something that you want to know or see.
3. Discuss higher-level questions or ideas on the riscv-debug-group mailing list: https://lists.riscv.org/g/tech-debug

For More Information
------------------

Additional information can be found at
https://github.com/riscv/debug-taskgroup
