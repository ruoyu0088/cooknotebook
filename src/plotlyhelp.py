def init_plotly_online_mode():
    from IPython.display import display_javascript
    from plotly import offline
    offline.offline.__PLOTLY_OFFLINE_INITIALIZED = True
    jscode = """
    require.config({
      paths: {
        d3: 'http://cdnjs.cloudflare.com/ajax/libs/d3/3.5.16/d3.min',
        plotly: 'http://cdn.plot.ly/plotly-1.10.0.min',
        jquery: 'https://code.jquery.com/jquery-migrate-1.4.1.min'
      },

      shim: {
        plotly: {
          deps: ['d3', 'jquery'],
          exports: 'plotly'
        }
      }
    });

    require(['d3', 'plotly'], function(d3, plotly) {
        window.Plotly = plotly;
    });
    """
    display_javascript(jscode, raw=True)


def plot_points(points, marker_size=3):
    from plotly.offline import iplot
    import plotly.graph_objs as go

    x, y, z = points[:3]

    trace1 = go.Scatter3d(
        x=x,
        y=y,
        z=z,
        mode='markers',
        marker=dict(size=marker_size)
    )

    data = [trace1]
    layout = go.Layout(
        margin=dict(l=0, r=0, b=0, t=0)
    )
    fig = go.Figure(data=data, layout=layout)
    iplot(fig)