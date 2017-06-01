def make_fullscreen_button():
    def javascript():
        style_center = """
        position:fixed;
        top:50%;
        left:50%;
        transform:translate(-50%, -50%);
        """

        style_full = """
        height:100vh;
        width:100vw;
        background-color:rgba(170, 170, 170, 0.9)
        ;z-index:100;"""

        html_full = '<div id="full_widget"><div id="center_widget"></div></div>'

        class FullWidget:
            def __init__(self):
                pass

            def fullscreen(self):
                self.widgets = jQuery(jQuery(".widget-area:visible")[-1])
                self.parents = self.widgets.parent()
                if len(jQuery("#full_widget")) > 0:
                    return
                jQuery(html_full).appendTo(jQuery('body'))
                jQuery('#full_widget').attr('style', style_full + style_center)
                jQuery('#center_widget').attr('style', style_center)
                self.widgets.appendTo(jQuery('#center_widget'))

                def on_key(event):
                    if event.which == 27:
                        self.cancel()

                jQuery("body").keydown(on_key)

            def cancel(self):
                if len(jQuery("#full_widget")) > 0:
                    self.widgets.insertAfter(self.parents.find(".input"))
                    jQuery('#full_widget').remove()
                    jQuery("body").unbind("kewdown")

        if not window.FullWidget:
            window.FullWidget = FullWidget
            window.full_widget = FullWidget()

    from flexx.pyscript import py2js
    from IPython.display import display_javascript
    js = py2js(javascript)
    run_js = "(function(){%s; javascript();})();" % js
    display_javascript(run_js, raw=True)

    from ipywidgets import Button, Layout
    button = Button(description="^", layout=Layout(width="15px"))

    def full_screen(event):
        from IPython.display import display_javascript, clear_output
        display_javascript("window.full_widget.fullscreen()", raw=True)
        clear_output()

    button.on_click(full_screen)
    return button


def load_ipython_extension(ip):
    from IPython.core.magic import register_cell_magic

    @register_cell_magic
    def py2js(line, cell):
        from flexx.pyscript import py2js
        from IPython.display import display_javascript
        js = py2js(cell)
        run_js = "(function(){%s})();" % js
        display_javascript(run_js, raw=True)