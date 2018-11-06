from datetime import timezone, datetime

from bokeh.layouts import widgetbox, layout

from model import propagate
from bokeh.server.server import Server
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource, TextInput, Button, DataTable, TableColumn


def compute(source, tle1, tle2):
    print("Computing...")
    source.data = ColumnDataSource(propagate(tle1, tle2, 5 * 86400, 60)).data


def create_figure(x, y, source, title):
    fig = figure(plot_width=400, plot_height=400, title=title, toolbar_location="below")
    fig.line(x=x, y=y, source=source)
    return fig


def modify_doc(doc):
    satellite = TextInput(title="Satellite:", value="TELSTAR 12V")
    tle1 = TextInput(title="TLE line 1:", value="1 41036U 15068A   18304.93002776 -.00000131  00000-0  00000-0 0  9990")
    tle2 = TextInput(title="TLE line 2:", value="2 41036   0.0170 254.0407 0001996 337.8139 128.1274  1.00270199 10707")

    maneuvers = ColumnDataSource(data=
                                 {"date": [datetime(2002, month=5, day=5, hour=12, minute=0, second=0, microsecond=0,
                                                    tzinfo=timezone.utc),
                                           datetime(2002, month=5, day=6, hour=12, minute=0, second=0, microsecond=0,
                                                    tzinfo=timezone.utc),
                                           datetime(2002, month=5, day=7, hour=12, minute=0, second=0, microsecond=0,
                                                    tzinfo=timezone.utc)],
                                  "deltaV_X": [100, 0, 0],
                                  "deltaV_Y": [0, 100, 0],
                                  "deltaV_Z": [0, 0, 100],
                                  "isp": [300, 300, 300]})
    maneuvers_table = DataTable(source=maneuvers, columns=[TableColumn(field="date", title="date"),
                                                           TableColumn(field="deltaV_X", title="deltaV_X"),
                                                           TableColumn(field="deltaV_Y", title="deltaV_Y"),
                                                           TableColumn(field="deltaV_Z", title="deltaV_Z")],
                                editable=True)

    ephemeris = ColumnDataSource()

    def recompute():
        compute(ephemeris, tle1.value, tle2.value)

    recompute()
    fig_long_sma = create_figure(x='longitude', y='a', source=ephemeris, title="SMA vs longitude")
    fig_ex_ey = create_figure(x='ex', y='ey', source=ephemeris, title="ex ey")
    fig_hx_hy = create_figure(x='hx', y='hy', source=ephemeris, title="hx hy")

    recompute_button = Button(label="Recompute")
    recompute_button.on_click(recompute)
    doc.add_root(layout([[widgetbox(satellite, tle1, tle2, recompute_button), widgetbox(maneuvers_table)],
                         [fig_long_sma, fig_ex_ey, fig_hx_hy]]))


server = Server({'/': modify_doc})
server.start()

if __name__ == '__main__':
    print('Opening Bokeh application on http://localhost:5006/')

    server.io_loop.add_callback(server.show, "/")
server.io_loop.start()
