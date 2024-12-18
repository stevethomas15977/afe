from models import TexasLandSurveySystem, TexasLandSurveySystemRepository


class TexasLandSurveySystemService:
    def __init__(self, db_path=None):
        self.repository = TexasLandSurveySystemRepository(db_path=db_path)

    def add(self, texas_land_survey_system_list: list[TexasLandSurveySystem]) -> None:
        self.repository.insert(texas_land_survey_system_list)

    def get_by_county_abstract(self, county: str, abstract: str) -> TexasLandSurveySystem:
        return self.repository.get_by_county_abstract(county=county, abstract=abstract)

    def get_by_county_abstract_block_section(self, county: str, abstract: str, block: str, section: str) -> TexasLandSurveySystem:
        return self.repository.get_by_county_abstract_block_section(county=county, abstract=abstract, block=block, section=section)

    def get_distinct_counties(self) -> list[str]:
        return self.repository.get_distinct_counties()
    
    def get_distinct_abstract_by_county(self, county: str) -> list[str]:
        return self.repository.get_distinct_abstract_by_county(county=county)
    
    def get_distinct_block_by_county_abstract(self, county: str, abstract: str) -> list[str]:
        return self.repository.get_distinct_block_by_county_abstract(county=county, abstract=abstract)
    
    def get_distinct_section_by_county_abstract_block(self, county: str, abstract: str, block: str) -> list[str]:
        return self.repository.get_distinct_section_by_county_abstract_block(county=county, abstract=abstract, block=block)
    
    def get_by_county(self, county: str) -> list:
        return self.repository.get_by_county(county=county)
    
    