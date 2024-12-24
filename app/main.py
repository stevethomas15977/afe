from http import HTTPStatus
from nicegui import ui, app, events, run
from helpers import ( texas_plss_block_section_overlay,
                     apply_geojson_overlay,
                     spc_feet_to_latlon,
                     write_to_file)
from services import ( NewMexicoLandSurveySystemService, TexasLandSurveySystemService )
from context import Context
import folium
import os, io, shutil, json, time
import tempfile
from pandas import isna, read_excel, DataFrame
from pathlib import Path
import threading
from workflow_manager import WorkflowManager
from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

passwords = {'afe-admin': os.environ['APP_SECRET']}

unrestricted_page_routes = {'/login', '/health'}

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not app.storage.user.get('authenticated', False):
            if not request.url.path.startswith('/_nicegui') and request.url.path not in unrestricted_page_routes:
                app.storage.user['referrer_path'] = request.url.path  # remember where the user wanted to go
                return RedirectResponse('/login')
        return await call_next(request)

app.add_middleware(AuthMiddleware)

class Project:
    def __init__(self):
        self.name = ''
        self.provider = 'Enverus'
        self.offset_well_file = None
        self.offset_survey_file = None
        self.state = None
        self.county = None
        self.abstract = None
        self.block = None
        self.tx_section = None
        self.township = None
        self.township_direction = None
        self.range = None
        self.range_direction = None
        self.nm_section = None
        self.system = 'NAD27'
        self.zone = 'Central'
        self.rows = []

    def to_dict(self):
        return {
            "name": self.name,
            "proivder": self.provider,
            "offset_well_file": self.offset_well_file,
            "offset_survey_file": self.offset_survey_file,
            "state": self.state,
            "county": self.county,
            "abstract": self.abstract,
            "block": self.block,
            "tx_section": self.tx_section,
            "township": self.township,
            "township_direction": self.township_direction,
            "range": self.range,
            "range_direction": self.range_direction,
            "nm_section": self.nm_section,
            "system": self.system,
            "zone": self.zone,
            "rows": self.rows
        }

target_well_columns = [
            {'headerName': 'ID', 'field': 'id', 'type': 'number', 'cellStyle':  {'textAlign': 'center'}},
            {'headerName': 'Name', 'field': 'name', 'editable': True, 'sortable': True, 'cellStyle':  {'textAlign': 'center'}},
            {'headerName': 'Surface X', 'field': 'surface_x', 'editable': True, 'type': 'number', 'cellStyle':  {'textAlign': 'center'}},
            {'headerName': 'Surface Y', 'field': 'surface_y', 'editable': True, 'type': 'number', 'cellStyle':  {'textAlign': 'center'}},
            {'headerName': 'Bottom Hole X', 'field': 'bottom_hole_x', 'editable': True, 'type': 'number', 'cellStyle':  {'textAlign': 'center'}},
            {'headerName': 'Bottom Hole Y', 'field': 'bottom_hole_y', 'editable': True, 'type': 'number', 'cellStyle':  {'textAlign': 'center'}},
            {'headerName': 'Landing Zone', 'field': 'lz', 'editable': True, 'sortable': True,  'cellStyle':  {'textAlign': 'center'}, 'cellEditor': 'agSelectCellEditor',
             'cellEditorParams': {'values': ['1BSSD','2BS','2BSSD','3BS','3BSSH','3BSSD','WXY','WAU','WAL','WBU','WBL','WC','WD']}},
            {'headerName': 'Perf Interval', 'field': 'perf_int', 'editable': True, 'type': 'number', 'cellStyle':  {'textAlign': 'center'}},
            {'headerName': 'SS Depth', 'field': 'ssd', 'editable': True, 'type': 'number', 'cellStyle':  {'textAlign': 'center'},
             'valueFormatter': 'value > 0 ? value * -1 : value'}
        ]

@ui.page('/')
async def index():
    with ui.header().classes('items-center justify-between'):
        with ui.button(icon='menu').style('height: 100%;'):
            with ui.menu():
                ui.menu_item('Create Project', lambda: create())
                ui.menu_item('View Projects', lambda: projects())

        header_label = ui.label(text=f'AFE Analysis').style('flex: 1; font-size: 150%; font-weight: 500')

        ui.add_head_html("""
            <style>
            .q-field__label {
                font-size: 1.8rem;
                font-style: bold;
                font-weight: 600;
                padding-bottom: 40px;
                width: 100%;
            }
            </style>
            """)
        
        ui.add_body_html('''
            <style>
            .ag-theme-balham {
                --ag-font-size: 20px;
                --ag-font-weight: bold;
                --ag-font-color: #000000;
            }
            </style>
            ''')  
    
        ui.add_css('''
            .ag-header-cell-label {
                justify-content: center;
                font-weight: bold;
            }
            ''')
        
    content_area = ui.column().style('width: 100%; padding: 20px;').classes('items-center justify-between') 
    with content_area:
        ui.button('Create Project', on_click=lambda: create()).classes('w-40')
        ui.button('View Projects', on_click=lambda: projects()).classes('w-40')
        
    footer = ui.footer().classes('items-center justify-between')

    context = Context()
    project = Project()
    
    def create():
        texas_land_survey_service = TexasLandSurveySystemService(context._texas_land_survey_system_database_path)
        new_mexico_land_survey_service = NewMexicoLandSurveySystemService(context._new_mexico_land_survey_system_database_path)

        def handle_file_upload(event: events.UploadEventArguments, file_type: str): 
            try:
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                temp_file.write(event.content.read())
                temp_file.close()
                if file_type == 'WELL_DATA':
                    project.offset_well_file = temp_file.name
                elif file_type == 'SURVEY_DATA':
                    project.offset_survey_file = temp_file.name
                
                ui.notify(f"Uploaded {event.name} successfully!", type='positive')
            except Exception as e:
                ui.notify(f"Failed to upload the file: {e}", type='negative')

        def add_row():
            new_id = max((dx['id'] for dx in project.rows), default=0) + 1
            project.rows.append({'id': new_id, 
                                 'name': '',
                                 'surface_x': 0, 
                                 'surface_y': 0, 
                                 'bottom_hole_x': 0, 
                                 'bottom_hole_y': 0, 
                                 'lz': '', 
                                 'perf_int': 0, 
                                 'ssd': 0})
            aggrid.update()

        def handle_cell_value_change(e):
            new_row = e.args['data']
            project.rows[:] = [row | new_row if row['id'] == new_row['id'] else row for row in project.rows]

        async def delete_selected():
            selected_id = [row['id'] for row in await aggrid.get_selected_rows()]
            project.rows[:] = [row for row in project.rows if row['id'] not in selected_id]
            aggrid.update()

        async def handle_state_change():
            if project.state == 'New Mexico':
                new_mexico_container.visible = True
                texas_container.visible = False
                counties = new_mexico_land_survey_service.get_distinct_counties()
            elif project.state == 'Texas':
                texas_container.visible = True
                new_mexico_container.visible = False
                counties = texas_land_survey_service.get_distinct_counties()
            county_select.clear()
            county_select.options = counties
            county_select.update()

        def handle_county_change():
            if project.state == 'Texas':
                abstracts = texas_land_survey_service.get_distinct_abstract_by_county(county_select.value)
                abstract_select.clear()
                abstract_select.options = abstracts
                abstract_select.update()
            elif project.state == 'New Mexico':
                townships = new_mexico_land_survey_service.get_distinct_townships_by_county(county_select.value)
                township_select.clear()
                township_select.options = townships
                township_select.update()

        def handle_abstract_change():
            blocks = texas_land_survey_service.get_distinct_block_by_county_abstract(project.county, project.abstract)
            block_select.clear()
            block_select.options = blocks
            block_select.update()

        def handle_block_change():
            sections = texas_land_survey_service.get_distinct_section_by_county_abstract_block(project.county, project.abstract, project.block)
            tx_section_select.clear()
            tx_section_select.options = sections
            tx_section_select.update()

        def handle_township_change():
            township_directions = new_mexico_land_survey_service.get_distinct_township_directions_by_county_township(project.county, project.township)
            township_direction_select.clear()
            township_direction_select.options = township_directions
            township_direction_select.update()

        def handle_township_direction_change():
            ranges = new_mexico_land_survey_service.get_distinct_ranges_by_county_township_range(project.county, project.township, project.township_direction)
            range_select.clear()
            range_select.options = ranges
            range_select.update()

        def handle_range_change(): 
            range_directions = new_mexico_land_survey_service.get_distinct_range_directions_by_county_township_township_direction_range(project.county, project.township, project.township_direction, project.range)
            range_direction_select.clear()
            range_direction_select.options = range_directions
            range_direction_select.update()

        def handle_range_direction_change():
            sections = new_mexico_land_survey_service.get_distinct_sections_by_county_township_township_direction_range_range_direction(project.county, project.township, project.township_direction, project.range, project.range_direction)
            new_mexico_section_select.clear()
            new_mexico_section_select.options = sections
            new_mexico_section_select.update()

        def handle_save():
            try:
                if project.name is None: 
                    ui.notify('Project name is empty', type='negative')
                    return
                
                if project.offset_well_file is None or project.offset_survey_file is None:
                    ui.notify('Please upload well and survey data files', type='negative')
                    return
                
                try:
                    context.project = project.name
                    context.project_path = os.path.join(context.projects_path, project.name)
                    os.makedirs(context.project_path, exist_ok=True)
                    
                    context.well_data_path = os.path.join(context.project_path, 'well_data')
                    context.survey_data_path = os.path.join(context.project_path, 'survey_data')

                    context.logs_path = os.path.join(context.project_path, 'logs')

                    os.makedirs(context.well_data_path, exist_ok=True)
                    os.makedirs(context.survey_data_path, exist_ok=True)
                    if os.path.exists(context.logs_path):
                        shutil.rmtree(context.logs_path)
                    os.makedirs(context.logs_path, exist_ok=True)

                    context.db_path = os.path.join(context.logs_path, f"{context.project}-{context.version}.db")

                except Exception as e:
                    ui.notify(f'Failed to create project directories: {e}', type='negative')
                    return
            
                for row in project.rows:
                    if not isna(row['surface_x']) and not isna(row['surface_y']) and not isna(row['bottom_hole_x']) and not isna(row['bottom_hole_y']):
                        context.target_well_information_file = os.path.join(context.logs_path, f'project.json')
                    
                try:
                    shutil.move(project.offset_well_file, os.path.join(context.well_data_path, f'{project.name}-well-data.xlsx'))
                    shutil.move(project.offset_survey_file, os.path.join(context.survey_data_path, f'{project.name}-survey-data.xlsx'))
                    context.well_file = os.path.join(context.well_data_path, f'{project.name}-well-data.xlsx')
                    context.survey_file = os.path.join(context.survey_data_path, f'{project.name}-survey-data.xlsx')   
                    with open(os.path.join(context.logs_path, 'project.json'), "w") as f:
                        json.dump(project.to_dict(), f, indent=4)
                except Exception as e:  
                    ui.notify(f'Failed to save files: {e}', type='negative')
                    return
                
                ui.notify(f"Project {project.name} saved successfully!", type='positive')
                project_files_container.visible = True
                project_files_container.clear()
                launch_workflow_button.visible = True
                with project_files_container:
                    ui.html(f'<iframe src="/projects/{project.name}" title="static" height="640px" width="1280px"></iframe>').style('width: 100%; height: 100%; border: none;')

            except Exception as e:
                ui.notify(f'Failed to save project: {e}', type='negative')

        def launch_workflow(context: Context):
            try:
                workflow_manager = WorkflowManager(context=context)
                workflow_thread = threading.Thread(name=context.project, target=execute_workflow, args=(workflow_manager, ))
                workflow_thread.start()
                spinner.visible = True
            except Exception as e:
                ui.notify(f'Failed to launch workflow: {e}', type='negative')

        def execute_workflow(workflow_manager: WorkflowManager):
            try:
                workflow_manager.project_initiation_workflow()
                workflow_manager.base_workflow()
                workflow_manager.offset_well_identification_workflow()
                if workflow_manager.context.target_well_information_file:
                    workflow_manager.gun_barrel_workflow()
                write_to_file(os.path.join(workflow_manager.context.project_path, f"COMPLETED"),f"Completed")
                spinner.visible = False
            except Exception as e:
                raise e

        content_area.clear()
        with content_area:

            with ui.column().style('width: 100%;').classes('justify-between'):

                project_name_container = ui.row().style('width: 100%;').classes('justify-left')
                with project_name_container:
                    ui.input(label='Name').style('font-size: 1.2rem').bind_value(project, 'name').classes('w-60')

                ui.separator()

                ui.label('Well Data Files').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
                offset_well_data_files_container = ui.row().style('width: 100%;').classes('justify-left')
                with offset_well_data_files_container:
                    ui.select(options=['Enverus'], label='Provider').style('font-size: 1.2rem').bind_value(project, 'provider').classes('w-40')            
                    well_data_upload = ui.upload(label='Well Data', on_upload=lambda event: handle_file_upload(event=event, file_type='WELL_DATA')).style('font-size: 1.2rem').classes('w-60')
                    survey_data_ulpload = ui.upload(label='Survey Data', on_upload=lambda event: handle_file_upload(event=event, file_type='SURVEY_DATA')).style('font-size: 1.2rem').classes('w-60')      

                ui.separator()

                ui.label('Target Wells').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
                
                ui.separator()

                surface_bottom_location_coordinates = ui.row().style('width: 100%;').classes('justify-left')
                with surface_bottom_location_coordinates:
                    system_select = ui.select(options=['NAD27', 'NAD83'],
                                            with_input=True,
                                            label='System').style('font-size: 1.2rem').bind_value(project, 'system').classes('w-40')
                    zone_select = ui.select(options=['East', 'Central', 'West'],
                                            with_input=True,
                                            label='Zone').style('font-size: 1.2rem').bind_value(project, 'zone').classes('w-40')
                    
                    ui.button('Delete selected', on_click=delete_selected)
                    ui.button('New row', on_click=add_row)

                    aggrid = ui.aggrid({
                        'columnDefs': target_well_columns,
                        'rowData': project.rows,
                        'rowSelection': 'multiple',
                        'stopEditingWhenCellsLoseFocus': True
                    }).on('cellValueChanged', handle_cell_value_change).classes('max-h-40')

                ui.separator()  

                ui.label('Target Well Bottom Hole Survey').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
                
                ui.separator()
                
                state_county_container = ui.row().style('width: 100%;').classes('justify-left')
                with state_county_container:
                    ui.select(options=['Texas', 'New Mexico'], 
                        with_input=True,
                        label='State',
                        on_change=lambda: handle_state_change()).bind_value(project, 'state').style('font-size: 1.2rem').classes('w-40')
                    county_select = ui.select(options=[], 
                        with_input=True,
                        label='County',
                        on_change=lambda: handle_county_change()).bind_value(project,'county').style('font-size: 1.2rem').classes('w-40')

                ui.separator()
                
                texas_container = ui.row().style('width: 100%;').classes('justify-left')
                with texas_container:
                    abstract_select = ui.select(options=[], 
                        with_input=True,
                        label='Abstract',
                        on_change=lambda: handle_abstract_change()).bind_value(project, 'abstract').style('font-size: 1.2rem').classes('w-40')
                
                    block_select = ui.select(options=[], 
                        with_input=True,
                        label='Block', 
                        on_change=lambda: handle_block_change()).style('font-size: 1.2rem').bind_value(project, 'block').classes('w-40')

                    tx_section_select = ui.select(options=[],
                        with_input=True,
                        label='Section').style('font-size: 1.2rem').bind_value(project, 'tx_section').classes('w-40')

                new_mexico_container = ui.row().style('width: 100%;').classes('justify-left')
                new_mexico_container.visible = False
                with new_mexico_container:
                    township_select = ui.select(options=[], 
                        with_input=True,
                        label='Township',
                        on_change=lambda: handle_township_change()).bind_value(project, 'township').style('font-size: 1.2rem').classes('w-50')
                    township_direction_select = ui.select(options=[],
                        with_input=True,
                        label='Townhip Direction',
                        on_change=lambda: handle_township_direction_change()).bind_value(project, 'township_direction').style('font-size: 1.2rem').classes('w-80')
                    range_select = ui.select(options=[],
                        with_input=True,
                        label='Range',
                        on_change=lambda: handle_range_change()).bind_value(project, 'range').style('font-size: 1.2rem').classes('w-40')
                    range_direction_select = ui.select(options=[],
                        with_input=True,
                        label='Range Direction',
                        on_change=lambda: handle_range_direction_change()).bind_value(project, 'range_direction').style('font-size: 1.2rem').classes('w-80')
                    new_mexico_section_select = ui.select(options=[],
                        with_input=True,
                        label='Section').style('font-size: 1.2rem').bind_value(project, 'nm_section').classes('w-40')
                
                ui.separator()

                bottom_save_container = ui.row().style('width: 100%;').classes('justify-left').bind_visibility_from(project, 'name')
                with bottom_save_container:
                    ui.button('Save', on_click=lambda: handle_save())
                    launch_workflow_button = ui.button('Launch Workflow', on_click=lambda: launch_workflow(context=context))
                    launch_workflow_button.visible = False
                    spinner = ui.spinner('hourglass', size='lg')
                    spinner.visible = False

                project_files_container = ui.expansion('Project Files', icon='description').classes('w-full').style('width: 100%; font-size: 1.3rem;')
                project_files_container.visible = False
                with project_files_container:
                    ui.space()

    def projects():

        def open_project(project_name): 
            context.project_path = os.path.join(context.projects_path, project_name)
            context.well_data_path = os.path.join(context.project_path, 'well_data')
            context.survey_data_path = os.path.join(context.project_path, 'survey_data')
            context.logs_path = os.path.join(context.project_path, 'logs')
            context.db_path = os.path.join(context.logs_path, f"{context.project}-{context.version}.db")
            
            try:
                with open(os.path.join(context.logs_path, 'project.json'), 'r') as f:
                    project = json.load(f)
                project_container.clear()
                with project_container:
                    ui.label(f'{project['name']}').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
            except Exception as e:
                ui.notify(f'Failed to open project: {e}', type='negative')
                return

            app.add_static_files(f"/{project_name}", context.project_path)

            files_container.clear()

            with files_container:   
                files = os.listdir(context.project_path)
                for file in files:
                    if os.path.isfile(os.path.join(context.project_path, file)):
                        ui.link(text=file, target=f'/{project_name}/{file}', new_tab=True).style('font-size: 1.2rem').classes('w-100')

                ui.separator()

                files = os.listdir(context.well_data_path)
                for file in files:
                    if os.path.isfile(os.path.join(context.well_data_path, file)):
                        ui.link(text=file, target=f'/{project_name}/well-data/{file}', new_tab=True).style('font-size: 1.2rem').classes('w-100')

                files = os.listdir(context.survey_data_path)
                for file in files:
                    if os.path.isfile(os.path.join(context.survey_data_path, file)):
                        ui.link(text=file, target=f'/{project_name}/survey-data/{file}', new_tab=True).style('font-size: 1.2rem').classes('w-100')

                ui.separator()
                
                files = os.listdir(context.logs_path)
                for file in files:
                    if os.path.isfile(os.path.join(context.logs_path, file)):
                        ui.link(text=file, target=f'/{project_name}/logs/{file}', new_tab=True).style('font-size: 1.2rem').classes('w-100')

        content_area.clear()
        with content_area:

            with ui.column().style('width: 100%;').classes('justify-between'):

                projects = os.listdir(context.projects_path)
                projects_container = ui.row().style('width: 100%;').classes('justify-left')
                with projects_container:
                    project_select = ui.select(options=projects, 
                                            label='Projects',
                                            with_input=True).style('font-size: 1.2rem').classes('w-40')
                    ui.button('Open', on_click=lambda: open_project(project_select.value))
                ui.separator()
                project_container = ui.row().style('width: 100%;').classes('justify-left')
                with project_container:
                    ui.space()

                ui.separator()
                files_container = ui.column().style('width: 100%;').classes('justify-left')
                with files_container:
                    ui.space()

@ui.refreshable
def time(project: str):
    directory = os.path.join(os.environ['PROJECTS_PATH'], project)
    app.add_static_files(f'/{project}', directory)
    files = os.listdir(directory)
    for file in files:
        if os.path.isfile(os.path.join(directory, file)):
            ui.link(text=file, target=f'/{project}/{file}', new_tab=True).style('font-size: 1.2rem').classes('w-100')

@ui.page('/projects/{project}')
def projects(project: str):
    time(project)
    ui.timer(15.0, lambda: time.refresh(project))

@app.api_route('/health', methods=['GET'])
def health():
    return HTTPStatus.OK

@ui.page('/login')
def login() -> Optional[RedirectResponse]:
    def try_login() -> None:  # local function to avoid passing username and password as arguments
        if passwords.get(username.value) == password.value:
            app.storage.user.update({'username': username.value, 'authenticated': True})
            ui.navigate.to(app.storage.user.get('referrer_path', '/'))  # go back to where the user wanted to go
        else:
            ui.notify('Wrong username or password', color='negative')

    if app.storage.user.get('authenticated', False):
        return RedirectResponse('/')
    with ui.card().classes('absolute-center'):
        username = ui.input('Username').on('keydown.enter', try_login)
        password = ui.input('Password', password=True, password_toggle_button=True).on('keydown.enter', try_login)
        ui.button('Log in', on_click=try_login)
    return None

ui.run(reload=False,
       host=os.environ['PRIVATE_IPV4'], 
       port=int(os.environ['HTTP_PORT']), 
       storage_secret=os.environ['APP_SECRET'],
       title='AFE Analysis')