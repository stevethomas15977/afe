from models import NewMexicoLandSurveySystem, NewMexicoLandSurveySystemRepository


class NewMexicoLandSurveySystemService:
    def __init__(self, db_path=None):
        self.repository = NewMexicoLandSurveySystemRepository(db_path=db_path)

    def get_by_county_township_range_section(self, county:str, township: int, township_direction: str, range: int, range_direction, section: int) -> NewMexicoLandSurveySystem:
        return self.repository.get_by_county_township_range_section(county=county, township=township, township_direction=township_direction, range=range, range_direction=range_direction, section=section)

    def get_distinct_counties(self) -> list:
        return self.repository.get_distinct_counties()
    
    def get_distince_townships_by_county(self, county: str) -> list:
        return self.repository.get_distinct_townships_by_county(county=county)
    
    def get_by_county(self, county: str) -> list:
        return self.repository.get_by_county(county=county)