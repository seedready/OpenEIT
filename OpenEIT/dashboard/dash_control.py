import dash 
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc
from . import page_not_found
from . import state 
from .modes import mode_names
from .modes import spectroscopy
from .modes import time_series
from .modes import imaging
from .modes import fw

class runGui(object):

    def __init__(self,controller):

        # Both controller and app have to be passed to the dynamically loaded page to enable callbacks and functionality with the rest of the package. 
        self.controller = controller
        self.app = None

        self.controller.register(
            "recording_state_changed",
            self.on_record_state_changed
        )

        self.controller.register(
            "connection_state_changed",
            self.on_connection_state_changed
        )

        self.connected = False
        self.recording = False 

        self.app = dash.Dash()
        self.app.css.config.serve_locally = True
        self.app.scripts.config.serve_locally = True
        # server = app.server
        self.app.config.suppress_callback_exceptions = True
                        
        # load it all up at the start so new routes aren't made after the server is started.                 
        self.bis_display = spectroscopy.BISgui(self.controller,self.app)
        self.bislayout = self.bis_display.return_layout()

        self.time_series_display = time_series.Timeseriesgui(self.controller,self.app)
        self.time_serieslayout = self.time_series_display.return_layout()        

        self.imaging_display = imaging.Tomogui(self.controller,self.app)
        self.imaginglayout = self.imaging_display.return_layout()   


        self.fw_display = fw.FWgui(self.controller,self.app)
        self.fwlayout = self.fw_display.return_layout()  


    def run(self):

        self.app.layout = html.Div([
            # stylesheet. 
            html.Link(
                rel='stylesheet',
                href='/static/bootstrap.min.css'
            ),

            # logo and brand name 
            html.Div([
                dcc.Link(
                html.Div([
                    html.Img(
                        src='/static/logo-white.png',
                        style={'height': 30, 'margin-right': 10}),
                    'OpenEIT Dashboard'
                ]),
                style={'margin-right': 40},
                className="navbar-brand",
                href='/'
                ),
                # navbar links
                html.Div(id='navbar-links', className='btn-group'),


                html.Div([
                    html.Pre('    '),
                    html.Button(
                        id='recordbutton',
                        className='btn btn-light'),
                    ], className='btn-group'),

            ], className='navbar navbar-expand-lg navbar-dark bg-dark'), 

            dcc.Location(id='url', refresh=False),




            # this is the page that appears when the buttons are pressed. 
            html.Div([
                html.Div(id='page-content')
            ], id='main-container', style={'margin': 15})

        ])

        # set_mode('')
        s = state.State()
        # the current state is none... which I suppose is ok. 
        print (s.mode)

        @self.app.server.route('/static/<path:path>')
        def static_file(path):
            static_folder = os.path.join(os.getcwd(), 'static')
            return send_from_directory(static_folder, path)

        @self.app.callback( 
            dash.dependencies.Output('recordbutton', 'children'),
            [dash.dependencies.Input('recordbutton', 'n_clicks')])
        def callback_dropdown(n_clicks):
            print ('savebutton callback')
            if n_clicks is not None:
                try: 
                    if self.recording == False:
                        print('start recording')
                        self.controller.start_recording()
                    else:
                        print ('stop recording')
                        self.controller.stop_recording()
                except: 
                    print('could not record')
                    self.recording = False 
            if self.recording is True: 
                return 'Stop Recording' 
            else:
                return 'Record'

        # This displays the page, it should also pass the app and controller info to the class. 
        @self.app.callback(Output('page-content', 'children'),
                      [Input('url', 'pathname')])
        def display_page(pathname):
            layout = page_not_found.layout
            for mode in mode_names:
                if pathname == mode.url:
                    print (mode.name)
                    s.set_mode(mode)
                    # instantiate the particular mode. 
                    if mode.name == 'Spectroscopy': 
                        layout = html.Div([self.bislayout])
                    elif mode.name == 'TimeSeries':
                        layout = html.Div([self.time_serieslayout ])
                    elif mode.name == 'Imaging':
                        layout = html.Div([self.imaginglayout])
                    else:
                        layout = html.Div([self.fwlayout])
            return layout

 
        @self.app.callback(Output('navbar-links', 'children'),
                      [Input('url', 'pathname')])
        def display_nav(pathname):
            navbar_links = []
            modes = mode_names
            for mode in modes:
                # print (mode.name)
                class_name = 'btn btn-outline-light'
                if mode and mode.url == pathname:
                    class_name = 'btn btn-light'
                link = dcc.Link(
                    mode.name,
                    id='{}-button'.format(mode.id),
                    className=class_name,
                    href=mode.url)
                navbar_links.append(link)

            return navbar_links

        self.app.run_server(debug=True)

    def on_connection_state_changed(self, connected):
        if connected:
            self.connected = True
        else:
            self.connected = False 

    def on_record_state_changed(self, recording):
        if recording:
            self.recording = True
        else:
            self.recording = False 
