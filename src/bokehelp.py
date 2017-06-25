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
