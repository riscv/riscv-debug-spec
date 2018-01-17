

## SW Proposal for using `ebreak`

The RISC-V ISA defines a single instruction, `ebreak` (or its compressed version `c.ebreak`) which can be configured by an external debugger to drop the core into Debug Mode. If no external debugger is attached, or if debugger has not configured the core to halt when `ebreak` is encountered, a hart which executes an `ebreak` raises a `breakpoint` exception. Note that the debugger can make this selection per execution mode (M, S, U). 

Neither the RISC-V ISA Specification nor the RISC-V Debug Specification defines how SW and/or external debuggers should use this instruction. This document is a proposal for how to use this instruction in various scenarios.

### Breakpoint

HW and/or SW debuggers can introduce `ebreak` instructions in order to create exception conditions which return to a more priviledged mode and/or external debugger. This usage is not described more here.

### SW Call to External Debugger

In some cases, the application code itself may intentionally want to halt and wait for the debugger. In this case, the application code itself can add `ebreak` to the code, where if an external debugger is connected and has set `dcsr` appropriately, the core will enter debug mode and halt. In order to distinguish this type of `ebreak` from the previous type, the following SW convention is proposed:

```
 .option norvc
 slli x0, x0, 0x1f
 ebreak
 srai x0, x0, <protocol>
 ```

Because the RISC-V ISA reserves the all-zero instruction as an illegal instruction, this instruction sequence will not generally occur in application code. `<protocol>` gives further information about the type of request and where additional arguments can be found.

| Protocol Value | Description  |
| -------------  |------------------|
| 0x5            | Arguments and command type are passed as for Linux System Calls|
| 0x7            | Arguments and command types are passed as for the ARM Semihosting Protocol|

### "Unreachable" Instruction

The compiler currently inserts `ebreak` instructions for the `_builtin_trap()` macro used for "should not reach" code. It is under discussion whether this is an appropriate mapping, or whether an illegal instruction may be more appropriate.

See an example at https://cx.rv8.io/g/xXgFX3.
