
def load_ipython_extension(ip):
    """Load the extension in IPython."""
    from IPython.display import display_javascript
    js = """
    Jupyter.CodeCell.options_default.highlight_modes["magic_text/x-csrc"] = 
        {'reg':['^%%cffi']};
    """
    display_javascript(js, raw=True)
    from .cffimagic import CffiMagic
    ip.register_magics(CffiMagic)
