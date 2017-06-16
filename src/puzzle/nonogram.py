from pyquery import PyQuery


def get_number(td):
    text = td.text_content()
    try:
        return int(text)
    except:
        return 0


def remove_zeros(data):
    return [[x for x in item if x != 0] for item in data]


def read_puzzle(filename):
    with open(filename) as f:
        html = f.read()
        pq = PyQuery(html)
    cols = list(zip(*[[get_number(td) for td in PyQuery(tr).find("td")] for tr in pq.find("td.nmtt tr")]))
    rows = [[get_number(td) for td in PyQuery(tr).find("td")] for tr in pq.find("td.nmtl tr")]
    cols = remove_zeros(cols)
    rows = remove_zeros(rows)
    return rows, cols