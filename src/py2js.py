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


def draw_nonogram_js(uid, parameter):
    cellwidth = 10
    ncols = len(parameter.cols)
    nrows = len(parameter.rows)
    width = ncols * cellwidth
    height = nrows * cellwidth

    def draw(Raphael):
        col_texts = []
        paper = Raphael(uid, width, height)
        col_texts = [paper.text(0, 0, "\n".join(col)) for col in parameter.cols]
        row_texts = [paper.text(0, 0, " ".join(row)) for row in parameter.rows]
        text_height = max([text.getBBox().height for text in col_texts])
        text_width = max([text.getBBox().width for text in row_texts])

        x0 = text_width + 10
        y0 = text_height + 10
        paper.setSize(x0 + ncols * cellwidth, y0 + nrows * cellwidth)

        for i, text in enumerate(col_texts):
            text.attr({"x": x0 + i * cellwidth + cellwidth / 2, "y":y0-5})
            box = text.getBBox()
            text.translate(0, -box.height/2)

        for i, text in enumerate(row_texts):
            text.attr({"x": x0 - 5, "y": y0 + i * cellwidth + cellwidth/2})
            text.attr({'text-anchor': 'end'})

        for x in range(ncols):
            for y in range(nrows):
                cell = paper.rect(x0 + x * cellwidth, y0 + y * cellwidth, cellwidth, cellwidth)
                fill = "#777777" if parameter.cells[y][x] else "#ffffff"
                cell.attr({"fill":fill, "stroke":"#cccccc"})

    require(['raphael'], draw)

def draw_nonogram(parameter):
    import json
    import uuid
    from IPython.display import display_html, display_javascript
    from flexx.pyscript import py2js

    parameter_js = json.dumps(parameter)
    uid = str(uuid.uuid1()).replace("-", "")
    display_html('<div id="{}"></div>'.format(uid), raw=True)
    jscode = py2js(draw_nonogram_js)
    run_js = "(function(parameter){%s; draw_nonogram_js('%s', parameter);})(%s);" % (jscode, uid, parameter_js)
    display_javascript(run_js, raw=True)


def py2js_call(func, parameter):
    import json
    import uuid
    from IPython.display import display_html, display_javascript
    from flexx.pyscript import py2js

    parameter_js = json.dumps(parameter)
    uid = str(uuid.uuid1()).replace("-", "")
    display_html('<div id="{}"></div>'.format(uid), raw=True)
    jscode = py2js(func)
    run_js = "(function(parameter){%s; %s('%s', parameter);})(%s);" % (jscode, func.__name__, uid, parameter_js)
    display_javascript(run_js, raw=True)


def load_ipython_extension(ip):
    from IPython.core.magic import register_cell_magic

    @register_cell_magic
    def py2js(line, cell):
        from flexx.pyscript import py2js
        from IPython.display import display_javascript
        from IPython import get_ipython
        pyvar = line.strip()
        ipy = get_ipython()
        if pyvar:
            parameter = ipy.ev(pyvar)
            if not isinstance(parameter, str):
                import json
                parameter = json.dumps(parameter)
        else:
            parameter = ""

        js = py2js(cell)
        run_js = "(function(parameter){%s})({%s});" % (js, parameter)
        display_javascript(run_js, raw=True)