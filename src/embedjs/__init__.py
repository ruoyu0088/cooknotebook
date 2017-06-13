from os import path

static_folder = path.join(path.dirname(__file__), "static")

resources = {
    "vis": ["vis.min.css", "vis.min.js"],
}

pre_process = {
    "vis.min.js": lambda s: s.replace('define.amd?define([],e)', 'define.amd?define("vis", [],e)')
}


def embed_resources(resources_name):
    from IPython.display import display_html
    output = []
    for fn in resources[resources_name]:
        with open(path.join(static_folder, fn), encoding="utf-8") as f:
            code = f.read()
            if fn in pre_process:
                code = pre_process[fn](code)

        if fn.endswith(".css"):
            output.append("<style>{}</style>".format(code))
        elif fn.endswith(".js"):
            output.append("<script>{}</script>".format(code))
    html = "\n".join(output)
    display_html(html, raw=True)

