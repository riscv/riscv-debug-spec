#!/usr/bin/env python2

import sys
import xml.etree.ElementTree
import argparse
import sympy
from sympy.functions.elementary.miscellaneous import Max
import math
import re
import collections

class Registers( object ):
    def __init__( self, name, label, prefix, description, skip_index,
            skip_access, skip_reset, depth ):
        self.name = name
        self.label = label
        self.prefix = prefix or ""
        self.description = description
        self.skip_index = skip_index
        self.skip_access = skip_access
        self.skip_reset = skip_reset
        self.depth = depth
        self.registers = []

    def add_register( self, register ):
        self.registers.append( register )

def sympy_compare_lowBit( a, b ):
    if sympy.simplify("(%s) > (%s)" % ( a.lowBit, b.lowBit )) == True:
        return 1
    if sympy.simplify("(%s) < (%s)" % ( a.lowBit, b.lowBit )) == True:
        return -1
    return 0

class Register( object ):
    def __init__( self, name, short, description, address, sdesc, define ):
        self.name = name
        self.short = short
        self.description = description
        self.address = address
        self.sdesc = sdesc
        self.define = define
        self.fields = []

        self.label = ( short or name ).lower() # TODO: replace spaces etc.

    def add_field( self, field ):
        self.fields.append( field )
        self.fields.sort( cmp=sympy_compare_lowBit, reverse=True )

    def check( self ):
        previous = None
        for f in self.fields:
            if not previous is None:
                expression = "(%s) > (%s)" % ( previous, f.highBit )
                result = sympy.simplify( expression )
                if type( result ) == bool:
                    assert result, "%s in %s of %s" % ( expression, f, self )

                expression = "(%s) - (%s)" % ( previous, f.highBit )
                delta = sympy.simplify( expression )
                try:
                    delta = int( delta )
                    assert delta == 1, \
                            "%s doesn't have all bits defined above %s (%s)" % ( self, f, expression )
                except TypeError:
                    pass
            previous = f.lowBit
        assert previous is None or int( previous ) == 0, \
                "%s isn't defined down to 0 (%r)" % ( self, previous )

    def width( self ):
        if self.fields:
            return Max(*(f.highBit for f in self.fields))
        else:
            return 0

    def __str__( self ):
        return self.name

class Field( object ):
    def __init__( self, name, lowBit, highBit, reset, access, description, sdesc, define ):
        self.name = name
        self.lowBit = lowBit
        self.highBit = highBit
        self.reset = reset
        self.access = access
        self.description = description
        self.define = define

    def length( self ):
        return sympy.simplify( "1 + (%s) - (%s)" % ( self.highBit, self.lowBit ) )

    def columnWidth( self ):
        text = str( self.length() )
        if text.isdigit():
            l = int( text )
        else:
            # Fancier would be to assume XLEN is 32 or something.
            l = 20
        return max( l, len( self.name ), len( self.lowBit + self.highBit ) * 1.2 )

    def __str__( self ):
        return self.name

def parse_bits( field ):
    """Return high, low (inclusive)."""
    text = field.get( 'bits' )
    parts = text.split( ':' )
    if len( parts ) == 1:
        return parts * 2
    elif len( parts ) == 2:
        return parts
    else:
        assert False, text

def parse_xml( path ):
    e = xml.etree.ElementTree.parse( path ).getroot()
    if e.text:
        description = e.text.strip()
    else:
        description = ""
    registers = Registers( e.get( 'name' ), e.get( 'label' ),
            e.get( 'prefix' ), description,
            int( e.get( 'skip_index', 0 ) ),
            int( e.get( 'skip_access', 0 ) ),
            int( e.get( 'skip_reset', 0 ) ),
            int( e.get( 'depth', 1 )))
    for r in e.findall( 'register' ):
        name = r.get( 'name' )
        short = r.get( 'short' )
        if r.text:
            description = r.text.strip()
        else:
            description = ""
        register = Register( name, short, description,
                r.get( 'address' ), r.get( 'sdesc' ),
                int( r.get( 'define', '1' ) ) )

        fields = r.findall( 'field' )
        for f in fields:
            highBit, lowBit = parse_bits( f )
            if f.text:
                description = f.text.strip()
            else:
                description = ""
            if f.get( 'name' ) == '0':
                define = int( f.get( 'define', '0' ) )
            else:
                define = int( f.get( 'define', '1' ) )
            field = Field( f.get( 'name' ), lowBit, highBit, f.get( 'reset' ),
                    f.get( 'access' ), description, f.get( 'sdesc' ),
                    define )
            register.add_field( field )

        register.check()
        registers.add_register( register )
    return registers

def toLatexIdentifier( text ):
    replacements = (
            ( '/', '' ),
            ( '\\_', '' ),
            ( ' ', '' ),
            ( '-', '' ),
            ( '(', '' ),
            ( ')', '' ),
            ( '64', 'sixtyfour' ),
            ( '32', 'thirtytwo' ),
            ( '28', 'twentyeight' ),
            ( '16', 'sixteen' ),
            ( '15', 'fifteen' ),
            ( '11', 'eleven' ),
            ( '9', 'nine' ),
            ( '8', 'eight' ),
            ( '7', 'seven' ),
            ( '6', 'six' ),
            ( '5', 'five' ),
            ( '4', 'four' ),
            ( '3', 'three' ),
            ( '2', 'two' ),
            ( '1', 'one' ),
            ( '0', 'zero' )
            )
    for frm, to in replacements:
        text = text.replace( frm, to )
    return text

def toCIdentifier( text ):
    return re.sub( "[^\w]", "_", text )

def write_definitions( fd, registers ):
    for r in registers.registers:
        if r.define:
            macroName = toLatexIdentifier( r.short or r.label )
            fd.write( "\\defregname{\\R%s}{\\hyperref[%s]{%s}}\n" % (
                macroName, r.label, r.short or r.label ) )
        for f in r.fields:
            if f.description and f.define:
                fd.write( "\\deffieldname{\\F%s}{\\hyperref[%s]{%s}}\n" % (
                        toLatexIdentifier( f.name ), f.name, f.name ) )

def write_cheader( fd, registers ):
    definitions = []
    for r in registers.registers:
        name = toCIdentifier( r.short or r.label ).upper()
        prefname = registers.prefix + name
        if r.define:
            definitions.append((prefname, r.address))
        try:
            if r.width() <= 32:
                suffix = "U"
            else:
                suffix = "ULL"
        except TypeError:
            suffix = "ULL"
        for f in r.fields:
            if f.define:
                if f.description:
                    definitions.append(( "comment", f.description ))
                offset = "%s_%s_OFFSET" % ( prefname, toCIdentifier( f.name ).upper() )
                length = "%s_%s_LENGTH" % ( prefname, toCIdentifier( f.name ).upper() )
                mask = "%s_%s" % ( prefname, toCIdentifier( f.name ).upper() )
                definitions.append(( offset, f.lowBit ))
                definitions.append(( length, f.length() ))
                try:
                    definitions.append(( mask,
                            "0x%x%s << %s" % ( ((1<<int(f.length()))-1), suffix, offset )))
                except TypeError:
                    definitions.append(( mask, "((1L<<%s)-1) << %s" % (f.length(), offset) ))

    counted = collections.Counter(name for name, value in definitions)
    for name, value in definitions:
        if name == "comment":
            fd.write( "/*\n" )
            for line in value.splitlines():
                fd.write( (" * %s" % line.strip()).strip() + "\n" )
            fd.write( " */\n" )
            continue
        if counted[name] == 1:
            if re.search(r"[\-\+<>]", str(value)):
                value = "(%s)" % value
            fd.write( "#define %-35s %s\n" % ( name, value ) )

def write_chisel( fd, registers ):
    fd.write("package freechips.rocketchip.devices.debug\n\n")
    fd.write("import Chisel._\n\n")

    fd.write("// This file was auto-generated from the repository at https://github.com/riscv/riscv-debug-spec.git,\n")
    fd.write("// 'make chisel'\n\n")

    fd.write("object " + registers.prefix + "RegAddrs {\n")

    for r in registers.registers:
        name = toCIdentifier( r.short or r.label ).upper()
        prefname = registers.prefix + name
        if (r.define and r.address):
            if r.description:
                fd.write ("  /* " + r.description + "\n  */\n")
            fd.write ("  def " + prefname + " =  "+ r.address + "\n\n")

    fd.write("}\n\n")

    for r in registers.registers:
        name = toCIdentifier( r.short or r.label ).upper()
 
        if (r.fields and r.define) :
            sorted_fields = sorted(r.fields, key = lambda x: int(x.lowBit), reverse = True)
            topbit = 31
            reserved = 0
            fd.write("class " + name + "Fields extends Bundle {\n\n")
            for f in sorted_fields:

                # These need try-catch blocks in the general case,
                # but for DM1 Registers it's fine.

                fieldlength = int(f.length())
                lowbit = int(f.lowBit)

                newtopbit = lowbit + fieldlength - 1

                if (newtopbit != topbit):
                    reservedwidth = topbit - newtopbit
                    print reserved
                    print reservedwidth
                    fd.write("  val reserved%d = UInt(%d.W)\n\n" % (reserved, reservedwidth))
                    reserved = reserved + 1
                if not f.define:
                    reservedwidth = fieldlength
                    fd.write("  val reserved%d = UInt(%d.W)\n\n" % (reserved, reservedwidth))
                    reserved = reserved + 1
                else:
                    if f.description:
                        fd.write("  /* " + f.description + "\n  */\n")

                    fd.write("  val " + toCIdentifier(f.name) + " = ")
                    if (int(fieldlength) > 1):
                        fd.write("UInt(%d.W)\n\n" % fieldlength)
                    else:
                        fd.write("Bool()\n\n")

                topbit = int(lowbit) - 1

            lastlowbit = int(sorted_fields[-1].lowBit)
            if (lastlowbit > 0 ):
                fd.write("  val reserved" + reserved + "= UInt(" + lastlowbit + ".W)\n")

            fd.write("}\n\n")

def address_value( address ):
    if type( address ) == str:
        try:
            return int( address, 0 )
        except ValueError:
            return address
    return address

def compare_address(a, b):
    try:
        return int(sympy.simplify("%s-(%s)" % (a, b)))
    except TypeError:
        return cmp(a, b)

def print_latex_index( registers ):
    print registers.description
    # Force this table HERE so that it doesn't get moved into the next section,
    # which will be the description of a register.
    print "\\begin{table}[H]"
    print "   \\begin{center}"
    print "      \\caption{%s}" % registers.name
    print "      \\label{%s}" % registers.label
    if any( r.sdesc for r in registers.registers ):
        print "      \\begin{tabular}{|r|l|l|l|}"
        print "      \\hline"
        print "      Address & Name & Description & Page \\\\"
    else:
        print "      \\begin{tabular}{|r|l|l|}"
        print "      \\hline"
        print "      Address & Name & Page \\\\"
    print "      \\hline"
    for r in sorted( registers.registers,
            cmp=lambda a, b: compare_address(a.address, b.address)):
        if r.short and (r.fields or r.description):
            page = "\\pageref{%s}" % r.short
        else:
            page = ""
        if r.short:
            name = "%s ({\\tt %s})" % (r.name, r.short)
        else:
            name = r.name
        if r.sdesc:
            print "%s & %s & %s & %s \\\\" % ( r.address, name, r.sdesc, page )
        else:
            print "%s & %s & %s \\\\" % ( r.address, name, page )
    print "         \hline"
    print "      \end{tabular}"
    print "   \end{center}"
    print "\end{table}"

def print_latex_custom( registers ):
    sub = "sub" * registers.depth
    for r in registers.registers:
        if not r.fields and not r.description:
            continue

        if r.short:
            if r.address:
                print "\\%ssection{%s ({\\tt %s}, at %s)}" % ( sub, r.name,
                        r.short, r.address )
            else:
                print "\\%ssection{%s ({\\tt %s})}" % ( sub, r.name, r.short )
            print "\index{%s}" % r.short
        else:
            if r.address:
                print "\\%ssection{%s (at %s)}" % ( sub, r.name, r.address )
            else:
                print "\\%ssection{%s}" % ( sub, r.name )
            print "\index{%s}" % r.name
        if r.label and r.define:
            print "\\label{%s}" % r.label
        print r.description
        print

        if r.fields:
            if all(f.access in ('R', '0') for f in r.fields):
                print "This entire register is read-only."

            print "\\begin{center}"

            totalWidth = sum( ( 3 + f.columnWidth() ) for f in r.fields )
            split = int( math.ceil( totalWidth / 80. ) )
            fieldsPerSplit = int( math.ceil( float( len( r.fields ) ) / split ) )
            subRegisterFields = []
            for s in range( split ):
                subRegisterFields.append( r.fields[ s*fieldsPerSplit : (s+1)*fieldsPerSplit ] )

            for registerFields in subRegisterFields:
                tabularCols = ""
                for f in registerFields:
                    fieldLength = str( f.length() )
                    lowLen = float( len( f.lowBit ) )
                    highLen = float( len( f.highBit ) )
                    tabularCols += "p{%.1f ex}" % ( f.columnWidth() * highLen / ( lowLen + highLen ) )
                    tabularCols += "p{%.1f ex}" % ( f.columnWidth() * lowLen / ( lowLen + highLen ) )
                print "\\begin{tabular}{%s}" % tabularCols

                first = True
                for f in registerFields:
                    if not first:
                        print "&"
                    first = False
                    if f.highBit == f.lowBit:
                        print "\\multicolumn{2}{c}{\\scriptsize %s}" % f.highBit
                    else:
                        print "{\\scriptsize %s} &" % f.highBit
                        print "\\multicolumn{1}{r}{\\scriptsize %s}" % f.lowBit

                # The actual field names
                print "\\\\"
                print "         \hline"
                first = True
                for f in registerFields:
                    if first:
                        cols = "|c|"
                    else:
                        cols = "c|"
                        print "&"
                    first = False
                    print "\\multicolumn{2}{%s}{$|%s|$}" % ( cols, f.name )
                print "\\\\"
                print "         \hline"

                # Size of each field in bits
                print " & ".join( "\\multicolumn{2}{c}{\\scriptsize %s}" % f.length() for f in registerFields )
                print "\\\\"

                print "   \\end{tabular}"

            print "\\end{center}"

        columns = [("l", "Field", "name")]
        columns += [("p{0.5\\textwidth}", "Description", "description")]
        if not registers.skip_access:
            columns += [("c", "Access", "access")]
        if not registers.skip_reset:
            columns += [("l", "Reset", "reset")]

        if any( f.description for f in r.fields ):
            print "\\tabletail{\\hline \\multicolumn{%d}{|r|}" % len(columns)
            print "   {{Continued on next page}} \\\\ \\hline}"
            print "\\begin{center}"
            print "   \\begin{longtable}{|%s|}" % "|".join(c[0] for c in columns)

            print "   \\hline"
            print "   %s\\\\" % " & ".join(c[1] for c in columns)
            print "   \\hline"
            print "   \\endhead"

            print "   \\multicolumn{%d}{r}{\\textit{Continued on next page}} \\\\" % \
                    len(columns)
            print "   \\endfoot"
            print "   \\endlastfoot"

            for f in r.fields:
                if f.description:
                    print "\\label{%s}" % f.name
                    print "\\index{%s}" % f.name
                    print "   |%s| &" % str(getattr(f, columns[0][2])),
                    print "%s\\\\" % " & ".join(str(getattr(f, c[2])) for c in columns[1:])
                    print "   \\hline"

            #print "   \\end{tabulary}"
            print "   \\end{longtable}"
            print "\\end{center}"
        print

def print_latex_register( registers ):
    print "%\usepackage{register}"
    sub = "sub" * registers.depth
    for r in registers.registers:
        if not r.fields and not r.description:
            continue

        if r.short:
            print "\\%ssection{%s (%s)}" % ( sub, r.name, r.short )
        else:
            print "\\%ssection{%s}" % ( sub, r.name )
        print r.description

        if not r.fields:
            continue
        print "\\begin{register}{H}{%s}{%s}" % ( r.name, r.address )
        print "   \\label{reg:%s}{}" % r.label
        for f in r.fields:
            length = f.length()
            if length is None:
                # If we don't know the length, draw it as 10 bits.
                length = 10
            print "   \\regfield{%s}{%d}{%s}{{%s}}" % (
                    f.name, length, f.lowBit, f.reset )

        print "   \\begin{regdesc}"
        print "      \\begin{reglist}"
        for f in r.fields:
            if f.description:
                print "      \\item[%s] (%s) %s" % ( f.name, f.access,
                        f.description )
        print "      \\end{reglist}"
        print "   \\end{regdesc}"

        print "\\end{register}"
        print

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument( 'path' )
    parser.add_argument( '--register', action='store_true',
            help='Use the LaTeX register module. No support for symbolic bit '
            'start/end positions.' )
    parser.add_argument( '--custom', action='store_true',
            help='Use custom LaTeX.' )
    parser.add_argument( '--definitions',
            help='Write register style definitions to the named file.' )
    parser.add_argument( '--cheader',
            help='Write C #defines to the named file.' )
    parser.add_argument( '--chisel',
            help='Write Scala Classes to the named file.' )
    parsed = parser.parse_args()

    registers = parse_xml( parsed.path )
    if parsed.definitions:
        write_definitions( file( parsed.definitions, "w" ), registers )
    if parsed.cheader:
        write_cheader( file( parsed.cheader, "w" ), registers )
    if parsed.chisel:
        write_chisel( file( parsed.chisel, "w" ), registers )
    if not registers.skip_index:
        print_latex_index( registers )
    if parsed.register:
        print_latex_register( registers )
    if parsed.custom:
        print_latex_custom( registers )

sys.exit( main() )
