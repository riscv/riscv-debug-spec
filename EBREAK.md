== SW Proposal for using `ebreak` ==

The RISC-V ISA defines a single instruction, `ebreak` (or its compressed version `c.ebreak`) which can be configured by an external debugger to drop the core into Debug Mode. It does not define how SW and/or external debuggers should use this instruction. This document is a proposal for how to use this instruction.

=== Breakpoint === 

This is fairly obvious/intuitive: HW and/or SW debuggers can introduce `ebreak` instructions in order to create exception conditions which return to a more priviledged mode and/or external debugger. This usage is not described more here.

=== SW Call to External Debugger === 

In some cases, the application code itself may intentionally want to halt and wait for the debugger. In this case, the application code itself can add `ebreak` to the code, where if an external debugger is connected and has set `dcsr` appropriately, the core will enter debug mode and halt. In order to distinguish this type of `ebreak` from the previous type, the following SW convention is proposed:

```
label   0x0 : ebreak
label + 0x4: 0x00000000
label + 0x8: <protocol>
label + 0xC: ...
```

Because the RISC-V ISA reserves the all-zero instruction as an illegal instruction, this instruction sequence will not generally occur in application code. `<protocol>` gives further information about the type of request and where additional arguments can be found.

| Protocol Value | Description  |
| -------------  |------------------|
| 0x5            | Arguments and command type are passed as for Linux System Calls|
| 0x7            | Arguments and command types are passed as for the ARM Semihosting Protocol|
