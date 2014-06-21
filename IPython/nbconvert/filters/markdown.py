"""Markdown filters
This file contains a collection of utility filters for dealing with 
markdown within Jinja templates.
"""
#-----------------------------------------------------------------------------
# Copyright (c) 2013, the IPython Development Team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# Imports
#-----------------------------------------------------------------------------
from __future__ import print_function

# Stdlib imports
import os
import subprocess
import warnings
from io import TextIOWrapper, BytesIO

try:
    import mistune
except ImportError:
    mistune = None

# IPython imports
from IPython.nbconvert.utils.pandoc import pandoc
from IPython.nbconvert.utils.exceptions import ConversionException
from IPython.utils.process import get_output_error_code
from IPython.utils.py3compat import cast_bytes
from IPython.utils.version import check_version

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
marked = os.path.join(os.path.dirname(__file__), "marked.js")
_node = None

__all__ = [
    'markdown2html',
    'markdown2html_pandoc',
    'markdown2html_marked',
    'markdown2html_mistune',
    'markdown2latex',
    'markdown2rst',
]

class NodeJSMissing(ConversionException):
    """Exception raised when node.js is missing."""
    pass

def markdown2latex(source):
    """Convert a markdown string to LaTeX via pandoc.

    This function will raise an error if pandoc is not installed.
    Any error messages generated by pandoc are printed to stderr.

    Parameters
    ----------
    source : string
      Input string, assumed to be valid markdown.

    Returns
    -------
    out : string
      Output as returned by pandoc.
    """
    return pandoc(source, 'markdown', 'latex')

def markdown2html(source):
    """Convert a markdown string to HTML"""
    global _node
    if _node is None:
        # prefer md2html via marked if node.js >= 0.9.12 is available
        # node is called nodejs on debian, so try that first
        _node = 'nodejs'
        if not _verify_node(_node):
            _node = 'node'
            if not _verify_node(_node):
                warnings.warn(  "Node.js 0.9.12 or later wasn't found.\n" +
                                "Nbconvert will try to use Pandoc instead.")
                _node = False
    if _node:
        return markdown2html_marked(source)
    if mistune is not None:
        return markdown2html_mistune(source)
    else:
        return markdown2html_pandoc(source)

if mistune is not None:
    from pygments import highlight
    from pygments.lexers import get_lexer_by_name
    from pygments.formatters import HtmlFormatter

    class MyRenderer(mistune.Renderer):
        def block_code(self, code, lang):
            if not lang:
                return '\n<pre><code>%s</code></pre>\n' % \
                    mistune.escape(code)
            lexer = get_lexer_by_name(lang, stripall=True)
            formatter = HtmlFormatter()
            return highlight(code, lexer, formatter)

def markdown2html_mistune(source):
    return mistune.Markdown(renderer=MyRenderer()).render(source)

def markdown2html_pandoc(source):
    """Convert a markdown string to HTML via pandoc"""
    return pandoc(source, 'markdown', 'html', extra_args=['--mathjax'])

def markdown2html_marked(source, encoding='utf-8'):
    """Convert a markdown string to HTML via marked"""
    command = [_node, marked]
    try:
        p = subprocess.Popen(command,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE
        )
    except OSError as e:
        raise NodeJSMissing(
            "The command '%s' returned an error: %s.\n" % (" ".join(command), e) +
            "Please check that Node.js is installed."
        )
    out, _ = p.communicate(cast_bytes(source, encoding))
    out = TextIOWrapper(BytesIO(out), encoding, 'replace').read()
    return out.rstrip('\n')

def markdown2rst(source):
    """Convert a markdown string to ReST via pandoc.

    This function will raise an error if pandoc is not installed.
    Any error messages generated by pandoc are printed to stderr.

    Parameters
    ----------
    source : string
      Input string, assumed to be valid markdown.

    Returns
    -------
    out : string
      Output as returned by pandoc.
    """
    return pandoc(source, 'markdown', 'rst')

def _verify_node(cmd):
    """Verify that the node command exists and is at least the minimum supported
    version of node.

    Parameters
    ----------
    cmd : string
        Node command to verify (i.e 'node')."""
    try:
        out, err, return_code = get_output_error_code([cmd, '--version'])
    except OSError:
        # Command not found
        return False
    if return_code:
        # Command error
        return False
    return check_version(out.lstrip('v'), '0.9.12')
