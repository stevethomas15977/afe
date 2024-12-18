from models import NewMexicoLandSurveySystem, NewMexicoLandSurveySystemRepository


class NewMexicoLandSurveySystemService:
    def __init__(self, db_path=None):
        self.repository = NewMexicoLandSurveySystemRepository(db_path=db_path)

    def get_by_county_township_range_section(self, county:str, township: int, township_direction: str, range: int, range_direction, section: int) -> NewMexicoLandSurveySystem:
        return self.repository.get_by_county_township_range_section(county=county, township=township, township_direction=township_direction, range=range, range_direction=range_direction, section=section)

    def get_distinct_counties(self) -> list:
        return self.repository.get_distinct_counties()
    
    def get_distinct_townships_by_county(self, county: str) -> list:
        return self.repository.get_distinct_townships_by_county(county=county)
    
    def get_distinct_township_directions_by_county_township(self, county: str, township: str) -> list:
        return self.repository.get_distinct_township_directions_by_county_township(county=county, township=township)
    
    def get_distinct_ranges_by_county_township_range(self, county: str, township: str, township_direction: str) -> list:
        return self.repository.get_distinct_ranges_by_county_township_range(county=county, township=township, township_direction=township_direction)
    
    def get_distinct_range_directions_by_county_township_township_direction_range(self, county: str, township: str, township_direction: str, range: int) -> list:
        return self.repository.get_distinct_range_directions_by_county_township_township_direction_range(county=county, township=township, township_direction=township_direction, range=range)
    
    def get_distinct_sections_by_county_township_township_direction_range_range_direction(self, county: str, township: str, township_direction: str, range: int, range_direction: str) -> list:
        return self.repository.get_distinct_sections_by_county_township_township_direction_range_range_direction(county=county, township=township, township_direction=township_direction, range=range, range_direction=range_direction)
    
    def get(self, county: str, township: str, township_direction: str, range: str, range_direction: str, section: str) -> NewMexicoLandSurveySystem:
        return self.repository.get(county=county, township=township, township_direction=township_direction, range=range, range_direction=range_direction, section=section)  
    
    def get_by_county(self, county: str) -> list:
        return self.repository.get_by_county(county=county)