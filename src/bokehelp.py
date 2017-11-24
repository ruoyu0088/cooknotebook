def copy_bokeh_resources():
    import os
    import shutil
    from os import path
    from bokeh.resources import INLINE

    for folder in ["static/js", "static/css"]:
        if not path.exists(folder):
            os.makedirs(folder)

    for fn in INLINE._file_paths("js"):
        shutil.copy(fn, "static/js")
    for fn in INLINE._file_paths("css"):
        shutil.copy(fn, "static/css")


def output_notebook():
    from bokeh.io import output_notebook
    from bokeh.resources import Resources

    output_notebook(Resources(mode="server", root_url="./"))


def show_figure(fig):
    from bokeh.document import Document
    from bokeh.io import curstate, show

    if fig.document is None:
        doc = Document()
        doc.add_root(fig)
        curstate().document = doc
    fig.__dict__["_handle"] = show(fig)


def update_figure(fig):
    from bokeh.io import push_notebook
    push_notebook(fig.document, None, fig._handle)


def make_quiver(fig, x, y, u, v, scale_uv=None, scale_arrow=0.4, theta=20):
    import numpy as np
    from bokeh.models import ColumnDataSource
    x, y, u, v = (np.asanyarray(arr).ravel() for arr in (x, y, u, v))
    if scale_uv is None:
        from scipy.spatial.distance import pdist, squareform
        mean_dist = np.mean(np.sort(squareform(pdist(np.c_[x, y])), axis=1)[:, 1])
        max_len = np.max(np.hypot(u, v))
        scale_uv = mean_dist / max_len

    theta = np.deg2rad(theta)
    m1 = np.array([[np.cos(theta), np.sin(-theta)], [np.sin(theta), np.cos(theta)]])
    m2 = np.array([[np.cos(theta), np.sin(theta)], [np.sin(-theta), np.cos(theta)]])
    u, v = u * scale_uv, v * scale_uv
    uv = np.vstack([u, v])
    u1, v1 = m1 @ uv * scale_arrow
    u2, v2 = m2 @ uv * scale_arrow
    data = ColumnDataSource(data=dict(x0=x, y0=y,
                                      x1=x+u, y1=y+v,
                                      x2=x+u-u1, y2=y+v-v1,
                                      x3=x+u-u2, y3=y+v-v2,
                                      u=u, v=v))
    fig.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=data)
    fig.segment(x0="x1", y0="y1", x1="x2", y1="y2", source=data)
    fig.segment(x0="x1", y0="y1", x1="x3", y1="y3", source=data)
    return data


class JS_RAW:
    def __init__(self, jscode):
        self.js_raw = [jscode]

    def __getattr__(self, name):
        return []


def show_figure_with_callback(fig, py_func, **env):
    import inspect
    from bokeh import embed
    from bokeh import resources
    from flexx.pyscript import py2js
    from jinja2 import Template

    args = list(inspect.signature(py_func).parameters.keys())

    template = Template("""
    setTimeout(
        function(){
            var fig = Bokeh.index['{{fig._id}}'];
            var doc = fig.model.document;
            {{py2js(py_func)}}
            {% for key, val in env.items() -%}
                {% if isinstance(val, str) %}
                    var {{key}} = {{val}};
                {% else %}
                    var {{key}} = doc.get_model_by_id('{{val._id}}');
                {% endif %}
            {% endfor %}
            {{py_func.__name__}}({{",".join(args)}});
        }
        , 10);
    """)
    template.globals.update(dict(isinstance=isinstance, py2js=py2js, str=str))

    jscode = template.render(py_func=py_func, fig=fig, env=env, args=args)


    embed.EMPTY = JS_RAW(jscode)
    try:
        show_figure(fig)
    finally:
        embed.EMPTY = resources.EMPTY


def compile_func(inputs):
    from flexx.pyscript import py2js

    if isinstance(inputs, str):
        return inputs

    wrap_code = """
    (function(){{
    {code}
    return {name};
    }})();
    """

    try:
        iter_funcs = iter(inputs)
    except TypeError:
        iter_funcs = iter([inputs])
    funcs = list(iter_funcs)
    code = "\n".join(py2js(func) for func in funcs)
    return wrap_code.format(code=code, name=funcs[-1].__name__)


def make_image_viewer(func, inputs, nx=100, x0=0, x1=1, ny=100, y0=0, y1=1,
                      plot_width=430, plot_height=400, sliders_width=300,
                      xlabel="x", ylabel="y", palette=None, image_type="image"):
    from itertools import cycle
    import numpy as np
    from bokeh.plotting import figure
    from bokeh.models import ColumnDataSource, Slider, LinearColorMapper, ColorBar, HoverTool
    from bokeh.models.callbacks import CustomJS
    from bokeh.layouts import widgetbox, row
    from bokeh.core import properties
    from bokeh import palettes

    dx = (x1 - x0) / (nx - 1)
    dy = (y1 - y0) / (ny - 1)

    if palette is None:
        palette = palettes.Viridis256

    for i, setting in enumerate(inputs):
        if not isinstance(setting, dict):
            name, start, end, step, *remain = setting
            value = remain[0] if remain else start
            inputs[i] = dict(title=name, start=start, end=end, step=step, value=value)

    for setting in inputs:
        if "name" not in setting:
            setting["name"] = setting["title"]

    sliders = [Slider(**setting) for setting in inputs]
    cmap = LinearColorMapper(palette, low=0, high=1)
    fig = figure(plot_width=plot_width, plot_height=plot_height, toolbar_location="above")

    if image_type == "image":
        source = ColumnDataSource(data=dict(z=[np.zeros((1, 1))],
                                            x=[x0], y=[y0],
                                            dx=[x1 - x0], dy=[y1 - y0]))
        fig.image("z", "x", "y", "dx", "dy", color_mapper=cmap, source=source)
    elif image_type == "rect":
        source = ColumnDataSource(data=dict(z=[0], x=[0], y=[0]))
        color = properties.field("z", cmap)
        fig.rect(x="x", y="y", width=dx, height=dy, fill_color=color, line_color=color, source=source)

    wbox = widgetbox(sliders, width=sliders_width)
    args = dict(nx=nx, x0=x0, x1=x1, ny=ny, y0=y0, y1=y1, dx=dx, dy=dy, image_type=image_type)

    source.tags = [dict(func=compile_func(func), args=args)]

    def callback(source=source, sliders=wbox, cmap=cmap):
        if isinstance(source.tags[0].func, str):
            source.tags[0].func = eval(source.tags[0].func)

        func = source.tags[0].func
        args = source.tags[0].args

        img = Float64Array(args.nx * args.ny)
        if args.image_type == "rect":
            xarr = Float64Array(args.nx * args.ny)
            yarr = Float64Array(args.nx * args.ny)

        data = source.data

        pars = dict([(slider.name, slider.value) for slider in sliders.children])

        i = 0
        for yi in range(args.ny):
            for xi in range(args.nx):
                x = xi * args.dx + args.x0
                y = yi * args.dy + args.y0
                img[i] = func(x, y, pars)
                if args.image_type == "rect":
                    xarr[i] = x
                    yarr[i] = y
                i += 1

        if args.image_type == "image":
            source.data.z[0] = img
            source._shapes.z[0] = [args.ny, args.nx]
        elif args.image_type == "rect":
            source.data.z = img
            source.data.x = xarr
            source.data.y = yarr
        cmap.low = min(img)
        cmap.high = max(img)
        source.change.emit()

    callback = CustomJS.from_py_func(callback)
    for slider in wbox.children:
        slider.js_on_change("value", callback)
    fig.js_on_change("inner_width", callback)
    fig.xaxis.axis_label = xlabel
    fig.yaxis.axis_label = ylabel

    if image_type == "image":
        fig.x_range.update(start=x0, end=x1)
        fig.y_range.update(start=y0, end=y1)
    elif image_type == "rect":
        fig.x_range.update(start=x0 - dx * 0.5, end=x1 + dx * 0.5)
        fig.y_range.update(start=y0 - dy * 0.5, end=y1 + dy * 0.5)
        hover = HoverTool(tooltips=[
            ("x, y, z", "@x, @y, @z"),
        ])
        fig.tools.append(hover)

    colorbar = ColorBar(color_mapper=cmap, label_standoff=12, border_line_color=None, location=(0,0))
    fig.add_layout(colorbar, 'right')
    return row(fig, wbox)