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