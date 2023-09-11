RISC-V Debug Specification
==========================

The current master branch is v1.0.0-stable.

You may be looking for one of the following pre-built PDFs:
* [Latest stable](https://github.com/riscv/riscv-debug-spec/blob/master/riscv-debug-stable.pdf)
* [Latest release](https://github.com/riscv/riscv-debug-spec/blob/release/riscv-debug-release.pdf)

Build Instructions
------------------

```
sudo apt-get install git make python3 python3-sympy graphviz texlive-full
make
```

There are two other interesting make targets:

1. `make debug_defines` creates a C header and implementation files containing
   constants for addresses and fields of all the registers and abstract
   commands, as well as function and structures used to decode register values.
   An implementation of such decoder can be seen in `debug_register_printers.c/h`.
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
