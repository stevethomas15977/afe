from nicegui import ui, events
from helpers import ( texas_plss_block_section_overlay,
                     apply_geojson_overlay,
                     spc_feet_to_latlon )
from services import ( NewMexicoLandSurveySystemService, TexasLandSurveySystemService )
from context import Context
import folium
import os, io
import tempfile
from pandas import isna, read_excel, DataFrame

class Project:
    def __init__(self):
        self.name = ''
        self.provider = 'Enverus'
        self.offset_well_file = None
        self.offset_survey_file = None
        self.state = 'Texas'
        self.county = None
        self.abstract = None
        self.block = None
        self.section = None
        self.township = None
        self.township_direction = None
        self.range = None
        self.range_direction = None
        self.new_mexico_section = None
        self.system = 'NAD27'
        self.zone = 'Central'
        self.columns = [
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
             'valueFormatter': 'value > 0 ? value * -1 : value'},
            {'field': 'surface_latitude', 'hide': True},
            {'field': 'surface_longitude', 'hide': True},
            {'field': 'bottom_hole_latitude', 'hide': True},
            {'field': 'bottom_hole_longitude', 'hide': True}
        ]
        self.rows = [
            {'id': 1, 
             'name': 'MOOSEHORN 54-1-41-44 G 61H', 
             'surface_x': 960823, 
             'surface_y': 832675, 
             'bottom_hole_x': 960499, 
             'bottom_hole_y': 821876, 
             'lz': '2BSS', 
             'perf_int': 10414, 
             'ssd': -6924, 
             'system': 'NAD27', 
             'zone': 'Central'}
        ]
        self.offset_wells = []

@ui.page('/')
def index():
    context = Context()
    texas_land_survey_service = TexasLandSurveySystemService(context._texas_land_survey_system_database_path)
    new_mexico_land_survey_service = NewMexicoLandSurveySystemService(context._new_mexico_land_survey_system_database_path)

    project = Project()

    def handle_file_upload(event: events.UploadEventArguments, file_type: str): 
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False)
            temp_file.write(event.content.read())
            temp_file.close()
            if file_type == 'WELL_DATA':
                project.offset_well_file = temp_file.name
                with open(project.offset_well_file, 'rb') as file:
                    bytes = file.read()
                columns, rows, row_key = validate_well_data(bytes=bytes)
                well_data_expansion.clear()
                with well_data_expansion:
                    ui.table(columns=columns, rows=rows, row_key=row_key, pagination=10).style('width: 100%; border: 1px solid black;')
                    project.offset_wells = rows
                    survey_data_ulpload.visible = True
            elif file_type == 'SURVEY_DATA':
                project.offset_survey_file = temp_file.name
            
            ui.notify(f"Uploaded {event.name} successfully!", type='positive')
        except Exception as e:
            ui.notify(f"Failed to upload the file: {e}", type='negative')

    def validate_well_data(bytes: bytes) -> tuple[list, list, str]:
        columns = []
        rows = []
        row_key = 'API_UWI'
        try:
            wells = read_excel(io.BytesIO(bytes), engine='openpyxl')

            wells = wells.sort_values(by=['LeaseName'], ascending=True)

            producing_wells = wells[wells["ENVWellboreStatus"] == "PRODUCING"]

            for column in producing_wells.columns:
                col_dict = dict()
                if column in well_headers():
                    col_dict['name'] = column
                    col_dict['label'] = column
                    col_dict['field'] = column
                    col_dict['required'] = True
                    col_dict['align'] = 'center'
                    columns.append(col_dict)                            

            for row in producing_wells.to_dict(orient='records'):
                row_dict = dict()

                try:
                    for header in well_headers():
                        if row.get(header) is None or isna(row.get(header)):
                            raise Exception(f"Missing value for {header}")
                except Exception as e:
                    continue
                
                if 'ENVInterval' == column:
                    if 'DELAWARE VERTICAL' == row.get(column):
                        continue
                for column in well_headers():
                    if column in well_headers():
                        if ('FirstProdDate' == column or 
                            'LastProducingMonth' == column):
                            if not isna(row.get(column)):
                                row_dict[column] = str(row.get(column).strftime("%Y-%m-%d"))
                            else:
                                row_dict[column] = None
                        else:
                            row_dict[column] = row.get(column)
                rows.append(row_dict)

        except Exception as e:
            raise Exception(f"Error validating Well Data: {str(e)}")
        
        return columns, rows, row_key
    
    def well_headers() -> list:
        return [
            "API_UWI",
            "WellName",
            "WellPadDirection",
            "ENVOperator",
            "ENVWellStatus",
            "LeaseName",
            "ENVInterval",
            "FirstProdDate",
            "Latitude",
            "Longitude",
            "Latitude_BH",
            "Longitude_BH",
            "TVD_FT",
            "MD_FT",
            "ElevationKB_FT",
            "LateralLength_FT",
            "PerfInterval_FT",
            "LateralLength_FT",
            "ProppantIntensity_LBSPerFT",
            "CumOil_BBL",
            "LastProducingMonth",
            "CumOil_BBLPer1000FT"
        ]
    
    def add_row():
        new_id = max((dx['id'] for dx in project.rows), default=-1) + 1
        project.rows.append({'id': new_id, 'name': '', 'age': None})
        ui.notify(f'Added row with ID {new_id}')
        aggrid.update()

    def handle_cell_value_change(e):
        new_row = e.args['data']
        ui.notify(f'Updated row to: {e.args["data"]}')
        project.rows[:] = [row | new_row if row['id'] == new_row['id'] else row for row in project.rows]

    async def delete_selected():
        selected_id = [row['id'] for row in await aggrid.get_selected_rows()]
        project.rows[:] = [row for row in project.rows if row['id'] not in selected_id]
        ui.notify(f'Deleted row with ID {selected_id}')
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
        section_select.clear()
        section_select.options = sections
        section_select.update()

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

    async def handle_section_change():
        coordinates = {}

        if project.state == 'Texas':
            if project.system == 'NAD27':
                inDatum = "NAD27"
                outDatum = "NAD27"
            elif project.system == 'NAD83':
                inDatum = "NAD83(2011)"
                outDatum = "NAD83(2011)"
            if project.zone == 'East':
                spcZone = 4203
            elif project.zone == 'Central':
                spcZone = 4203
            elif project.zone == 'West':
                spcZone = 4203

            for row in project.rows:
                if row['surface_x'] is not None and row['surface_y'] is not None:
                    surface_latitude, surface_longitude = spc_feet_to_latlon(northing=row['surface_y'], 
                                                                            easting=row['surface_x'],
                                                                            spcZone=spcZone,
                                                                            inDatum=inDatum)
                    row['surface_latitude'] = surface_latitude
                    row['surface_longitude'] = surface_longitude
                if row['bottom_hole_x'] is not None and row['bottom_hole_y'] is not None:
                    bottom_hole_latitude, bottom_hole_longitude = spc_feet_to_latlon(northing=row['bottom_hole_y'], 
                                                                            easting=row['bottom_hole_x'],
                                                                            spcZone=spcZone,
                                                                            inDatum=inDatum)
                    row['bottom_hole_latitude'] = bottom_hole_latitude
                    row['bottom_hole_longitude'] = bottom_hole_longitude
                
        elif project.state == 'New Mexico':
            pass

        if project.state == 'Texas':
            survey = texas_land_survey_service.get_by_county_abstract_block_section(project.county, project.abstract, project.block, project.section)
        elif project.state == 'New Mexico':
            survey = new_mexico_land_survey_service.get_by_county_township_range_section(project.county, project.township, project.township_direction, project.range, project.range_direction, project.new_mexico_section)

        if survey is None:
            return
        
        if survey.southwest_latitude is not None and survey.southwest_longitude is not None:
            center = (survey.southwest_latitude, survey.southwest_longitude)
        elif survey.southeast_latitude is not None and survey.southeast_longitude is not None:
            center = (survey.southeast_latitude, survey.southeast_longitude)
        elif survey.northwest_latitude is not None and survey.northwest_longitude is not None:
            center = (survey.northwest_latitude, survey.northwest_longitude)            
        elif survey.northeast_latitude is not None and survey.northeast_longitude is not None:
            center = (survey.northeast_latitude, survey.northeast_longitude)
        
        if survey.southwest_latitude is not None and survey.southwest_longitude is not None:
            coordinates['southwest_latitude'] = survey.southwest_latitude
            coordinates['southwest_longitude'] = survey.southwest_longitude
        if survey.southeast_latitude is not None and survey.southeast_longitude is not None:
            coordinates['southeast_latitude'] = survey.southeast_latitude
            coordinates['southeast_longitude'] = survey.southeast_longitude
        if survey.northwest_latitude is not None and survey.northwest_longitude is not None:
            coordinates['northwest_latitude'] = survey.northwest_latitude
            coordinates['northwest_longitude'] = survey.northwest_longitude
        if survey.northeast_latitude is not None and survey.northeast_longitude is not None:
            coordinates['northeast_latitude'] = survey.northeast_latitude
            coordinates['northeast_longitude'] = survey.northeast_longitude

        map_container.clear()
        map_container.update()
        with map_container:
            map = folium.Map(location=[center[0], center[1]],
                           zoom_start=14,
                           tiles='OpenStreetMap')

            if project.state == 'Texas':
                # Draw the Texas PLSS Overlay
                fips_codes = []
                fips_codes.append(survey.fips_code)
                texas_plss_block_section_overlay(context=context, abstract=project.abstract, fip_codes=fips_codes, map=map)
                # Draw the section lines
                tooltip = f"{survey.abstract}-{survey.block}-{str(int(survey.section))}"
            elif project.state == 'New Mexico':
                # Draw the New Mexico PLSS Overlay
                new_mexico_township_file_path = os.path.join(context.geojson_path, 'new_mexico', 'PLSSTownship.geojson')
                apply_geojson_overlay(new_mexico_township_file_path, name='PLSS Townships', label='TWNSHPLAB', map=map)
                new_mexico_sections_file_path = os.path.join(context.geojson_path, 'new_mexico', 'sections')
                geojson_file = f"{survey.township}{survey.township_direction}-{survey.range}{survey.range_direction}.geojson"
                apply_geojson_overlay(geojson_file_path=os.path.join(new_mexico_sections_file_path, geojson_file), name='PLSS Sections', label=context.nm_section_column, map=map)
                tooltip = f"{project.township}-{project.township_direction}-{project.range}-{project.range_direction}-{project.section}"

            # Draw the section lines
            if (coordinates.get('southwest_latitude') is not None and 
                coordinates.get('southwest_longitude') is not None and
                coordinates.get('southeast_latitude') is not None and
                coordinates.get('southeast_longitude') is not None):
                start = (coordinates['southwest_latitude'], coordinates['southwest_longitude'])
                end = (coordinates['southeast_latitude'], coordinates['southeast_longitude'])
                folium.PolyLine([start, end], color='black', tooltip=tooltip, weight=3.0).add_to(map)
            if (coordinates.get('southeast_latitude') is not None and
                coordinates.get('southeast_longitude') is not None and
                coordinates.get('northeast_latitude') is not None and
                coordinates.get('northeast_longitude') is not None):
                start = (coordinates['southeast_latitude'], coordinates['southeast_longitude'])
                end = (coordinates['northeast_latitude'], coordinates['northeast_longitude'])
                folium.PolyLine([start, end], color='black', tooltip=tooltip, weight=3.0).add_to(map)
            if (coordinates.get('northeast_latitude') is not None and
                coordinates.get('northeast_longitude') is not None and
                coordinates.get('northwest_latitude') is not None and
                coordinates.get('northwest_longitude') is not None):
                start = (coordinates['northeast_latitude'], coordinates['northeast_longitude'])
                end = (coordinates['northwest_latitude'], coordinates['northwest_longitude'])
                folium.PolyLine([start, end], color='black', tooltip=tooltip, weight=3.0).add_to(map)
            if (coordinates.get('northwest_latitude') is not None and
                coordinates.get('northwest_longitude') is not None and
                coordinates.get('southwest_latitude') is not None and
                coordinates.get('southwest_longitude') is not None):
                    start = (coordinates['northwest_latitude'], coordinates['northwest_longitude'])
                    end = (coordinates['southwest_latitude'], coordinates['southwest_longitude'])
                    folium.PolyLine([start, end], color='black', tooltip=tooltip, weight=3.0).add_to(map)

            # Draw target wells
            for row in project.rows:
                if (row['surface_latitude'] is not None and 
                    row['surface_longitude'] is not None and
                    row['bottom_hole_latitude'] is not None and
                    row['bottom_hole_longitude'] is not None):
                        start = (float(row['surface_latitude']), float(row['surface_longitude']))
                        end = (float(row['bottom_hole_latitude']), float(row['bottom_hole_longitude']))
                        folium.PolyLine([start, end], color="orange", weight=3.0).add_to(map)
                
                        folium.Marker(
                            location=start,
                            icon=folium.DivIcon(icon_size=(150, 36), 
                                icon_anchor=(0, 0),
                                html=f'<div style="font-size: 20px; color: black;"><b></b></div>'
                            ),).add_to(map)
                        
            # Draw offset wells
            for row in project.offset_wells:
                start = (float(row['Latitude']), float(row['Longitude']))
                end = (float(row['Latitude_BH']), float(row['Longitude_BH']))
                folium.PolyLine([start, end], color="green", weight=3.0).add_to(map)
                folium.Marker(
                    location=start,
                    icon=folium.DivIcon(icon_size=(150, 36), 
                        icon_anchor=(0, 0),
                        html=f'<div style="font-size: 20px; color: black;"><b></b></div>'
                    ),).add_to(map)

            # Convert the map to HTML
            map_html = map._repr_html_()
            # Display the map in NiceGUI
            map_container.set_content(map_html)

    with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
        ui.label('AFE Analysis').style('color: white; font-size: 1.5rem')

    with ui.column().style('width: 100%;').classes('justify-between'):

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
    
        ui.label('Project Name').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
        project_name_container = ui.row().style('width: 100%;').classes('justify-left')
        with project_name_container:
            ui.input(label='Name', on_change=lambda: handle_section_change()).style('font-size: 1.2rem').bind_value(project, 'name').classes('w-60')
        ui.separator()

        ui.label('Offset Well Data Files').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
        offset_well_data_files_container = ui.row().style('width: 100%;').classes('justify-left')
        with offset_well_data_files_container:
            ui.select(options=['Enverus'], label='Provider').style('font-size: 1.2rem').bind_value(project, 'provider').classes('w-40')            
            well_data_upload = ui.upload(label='Well Data', on_upload=lambda event: handle_file_upload(event=event, file_type='WELL_DATA')).style('font-size: 1.2rem').classes('w-60')
            survey_data_ulpload = ui.upload(label='Survey Data', on_upload=lambda event: handle_file_upload(event=event, file_type='SURVEY_DATA')).style('font-size: 1.2rem').classes('w-60')      
            survey_data_ulpload.visible = False

            well_data_expansion = ui.expansion('Well Data', icon='oil_barrel').classes('w-full').style('width: 100%; font-size: 1.3rem;')
            with well_data_expansion:
                ui.space()

        ui.separator()

        ui.label('Target Well Information').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
        ui.separator()

        surface_bottom_location_coordinates = ui.row().style('width: 100%;').classes('justify-left')
        with surface_bottom_location_coordinates:
            system_select = ui.select(options=['NAD27', 'NAD83'],
                                    with_input=True,
                                    label='System',
                                    on_change=lambda: handle_section_change()).style('font-size: 1.2rem').bind_value(project, 'system').classes('w-40')
            zone_select = ui.select(options=['East', 'Central', 'West'],
                                    with_input=True,
                                    label='Zone',
                                    on_change=lambda: handle_section_change()).style('font-size: 1.2rem').bind_value(project, 'zone').classes('w-40')
            
            aggrid = ui.aggrid({
                'columnDefs': project.columns,
                'rowData': project.rows,
                'rowSelection': 'multiple',
                'stopEditingWhenCellsLoseFocus': True,
            }).on('cellValueChanged', handle_cell_value_change).classes('max-h-40')

            ui.button('Delete selected', on_click=delete_selected)
            ui.button('New row', on_click=add_row)

        ui.separator()  

        ui.label('Bottom Hole Survey Information').style('font-size: 1.8rem').classes('w-100').style('font-weight: bold;')
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

            section_select = ui.select(options=[],
                with_input=True,
                label='Section',
                on_change=lambda: handle_section_change()).style('font-size: 1.2rem').bind_value(project, 'section').classes('w-40')

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
                on_change=lambda: handle_range_change()).bind_value(project, 'range').style('font-size: 1.2rem').classes('w-50')
            range_direction_select = ui.select(options=[],
                with_input=True,
                label='Range Direction',
                on_change=lambda: handle_range_direction_change()).bind_value(project, 'range_direction').style('font-size: 1.2rem').classes('w-80')
            new_mexico_section_select = ui.select(options=[],
                with_input=True,
                label='Section',
                on_change=lambda: handle_section_change()).style('font-size: 1.2rem').bind_value(project, 'new_mexico_section').classes('w-40')

        ui.separator()

        with ui.expansion('Surface Map', icon='map').classes('w-full').style('width: 100%; font-size: 1.3rem;'):
            map_container = ui.html().style('width: 100%; height: 800px;').classes('justify-between')
            with map_container:
                ui.space()

    with ui.footer().style('background-color: #3874c8'):
        ui.label('')

ui.run()