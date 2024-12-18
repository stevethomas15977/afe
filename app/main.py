from nicegui import ui
from services import TexasLandSurveySystemService
from context import Context
from models import TexasLandSurveySystem
from helpers import ( texas_plss_block_section_overlay,
                     draw_section_lines )
import folium

class Project:
    def __init__(self):
        self.state = 'Texas'
        self.county = None
        self.abstract = None
        self.block = None
        self.section = None
        self.system = 'NAD83'
        self.zone = 'Central'

@ui.page('/')
def index():
    context = Context()
    texas_land_survey_service = TexasLandSurveySystemService(context._texas_land_survey_system_database_path)

    project = Project()

    def handle_county_change():
        abstracts = texas_land_survey_service.get_distinct_abstract_by_county(county_select.value)
        abstract_select.clear()
        abstract_select.options = abstracts
        abstract_select.update()

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

    async def handle_section_change():
        coordinates = {}
        survey = texas_land_survey_service.get_by_county_abstract_block_section(project.county, project.abstract, project.block, project.section)
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
            # Draw the Texas PLSS Block Section Overlay
            fips_codes = []
            fips_codes.append(survey.fips_code)
            texas_plss_block_section_overlay(context=context, fip_codes=fips_codes, map=map)
            
            # Draw the section lines
            tooltip = f"{survey.abstract}-{survey.block}-{str(int(survey.section))}"

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
                font-syle: bold;
                font-weight: 600;
                padding-bottom: 40px;
                width: 100%;
            }
            </style>
            """)
        ui.label('Botton Hole Survey Information').style('font-size: 1.8rem').classes('w-100')
        ui.separator()
        
        counties = texas_land_survey_service.get_distinct_counties()
        county_container = ui.column().style('width: 100%;').classes('justify-between')
        with county_container:
            county_select = ui.select(options=counties, 
                with_input=True,
                label='County',
                on_change=lambda: handle_county_change()).bind_value(project,'county').style('font-size: 1.2rem').classes('w-40')
        ui.separator()
        
        abstract_container = ui.column().style('width: 100%;').classes('justify-between')
        with abstract_container:
            abstract_select = ui.select(options=[], 
                with_input=True,
                label='Abstract',
                on_change=lambda: handle_abstract_change()).bind_value(project, 'abstract').style('font-size: 1.2rem').classes('w-40')
        ui.separator()
        
        block_container = ui.column().style('width: 100%;').classes('justify-between')
        with block_container:
            block_select = ui.select(options=[], 
                with_input=True,
                label='Block', 
                on_change=lambda: handle_block_change()).style('font-size: 1.2rem').bind_value(project, 'block').classes('w-40')
        ui.separator()
        
        section_container = ui.column().style('width: 100%;').classes('justify-between')
        with section_container:
            section_select = ui.select(options=[],
                with_input=True,
                label='Section',
                on_change=lambda: handle_section_change()).style('font-size: 1.2rem').bind_value(project, 'section').classes('w-40')
        ui.separator()  

        map_container = ui.html().style('width: 100%; height: 800px;').classes('justify-between')
        with map_container:
            ui.space()

    with ui.footer().style('background-color: #3874c8'):
        ui.label('')

ui.run()