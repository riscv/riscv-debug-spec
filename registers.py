#!/usr/bin/env python

import sys
import xml.etree.ElementTree
import argparse
import sympy
import math
import re

class Registers( object ):
    def __init__( self, name, label, description, skip_index, skip_access, skip_reset ):
        self.name = name
        self.label = label
        self.description = description
        self.skip_index = skip_index
        self.skip_access = skip_access
        self.skip_reset = skip_reset
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
    registers = Registers( e.get( 'name' ), e.get( 'label' ), description,
            int( e.get( 'skip_index', 0 ) ),
            int( e.get( 'skip_access', 0 ) ),
            int( e.get( 'skip_reset', 0 ) ) )
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
            ( '(', '' ),
            ( ')', '' ),
            ( '64', 'sixtyfour' ),
            ( '32', 'thirtytwo' ),
            ( '28', 'twentyeight' ),
            ( '16', 'sixteen' ),
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
                fd.write( "\\deffieldname{\\F%s}{%s}\n" % (
                        toLatexIdentifier( f.name ), f.name ) )

def write_cheader( fd, registers ):
    for r in registers.registers:
        name = toCIdentifier( r.short or r.label ).upper()
        if r.define:
            fd.write( "#define %s_ADDRESS  %s\n" % ( name, r.address ) )
        for f in r.fields:
            if f.define:
                offset = "%s_%s_OFFSET" % ( name, toCIdentifier( f.name ).upper() )
                mask = "%s_%s_MASK" % ( name, toCIdentifier( f.name ).upper() )
                fd.write( "#define %s %s\n" % ( offset, f.lowBit ) )
                fd.write( "#define %s (((1<<%s)-1) << %s)\n" % ( mask, f.length(), offset ) )

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
    print "\\begin{table}[htp]"
    print "   \\begin{center}"
    print "      \\caption{%s}" % registers.name
    print "      \\label{%s}" % registers.label
    if any( r.sdesc for r in registers.registers ):
        print "      \\begin{tabular}{|r|l|l|}"
        print "      \\hline"
        print "      Address & Name & Description \\\\"
    else:
        print "      \\begin{tabular}{|r|l|}"
        print "      \\hline"
        print "      Address & Name \\\\"
    print "      \\hline"
    for r in sorted( registers.registers,
            cmp=lambda a, b: compare_address(a.address, b.address)):
        if r.sdesc:
            print "%s & %s & %s \\\\" % ( r.address, r.name, r.sdesc )
        else:
            print "%s & %s \\\\" % ( r.address, r.name )
    print "         \hline"
    print "      \end{tabular}"
    print "   \end{center}"
    print "\end{table}"

def print_latex_custom( registers ):
    for r in registers.registers:
        if not r.fields and not r.description:
            continue

        if r.short:
            if r.address:
                print "\\subsubsection{%s ({\\tt %s}, at %s)}" % ( r.name, r.short, r.address )
            else:
                print "\\subsubsection{%s ({\\tt %s})}" % ( r.name, r.short )
        else:
            if r.address:
                print "\\subsubsection{%s (at %s)}" % ( r.name, r.address )
            else:
                print "\\subsubsection{%s}" % r.name
        if r.label and r.define:
            print "\\label{%s}" % r.label
        print r.description

        if r.fields:
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
            print "   \\begin{xtabular}{|%s|}" % "|".join(c[0] for c in columns)
            print "   \\hline"
            print "   %s\\\\" % " & ".join(c[1] for c in columns)
            print "   \\hline"
            for f in r.fields:
                if f.description:
                    print "   |%s| &" % str(getattr(f, columns[0][2])),
                    print "%s\\\\" % " & ".join(str(getattr(f, c[2])) for c in columns[1:])
                    print "   \\hline"

            #print "   \\end{tabulary}"
            print "   \\end{xtabular}"
            print "\\end{center}"
        print

def print_latex_register( registers ):
    print "%\usepackage{register}"
    for r in registers.registers:
        if not r.fields and not r.description:
            continue

        if r.short:
            print "\\subsubsection{%s (%s)}" % ( r.name, r.short )
        else:
            print "\\subsubsection{%s}" % r.name
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
    parsed = parser.parse_args()

    registers = parse_xml( parsed.path )
    if parsed.definitions:
        write_definitions( file( parsed.definitions, "w" ), registers )
    if parsed.cheader:
        write_cheader( file( parsed.cheader, "w" ), registers )
    if not registers.skip_index:
        print_latex_index( registers )
    if parsed.register:
        print_latex_register( registers )
    if parsed.custom:
        print_latex_custom( registers )

sys.exit( main() )
