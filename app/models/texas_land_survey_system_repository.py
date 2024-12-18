from sqlite3 import Connection, Cursor, DatabaseError, IntegrityError

from database import AFEDB
from models import TexasLandSurveySystem


class TexasLandSurveySystemRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = Connection(db_path)

    def __del__(self):
        self.connection.close()

    def insert(self, texas_land_survey_system_list: list[TexasLandSurveySystem]):
        try:
            cursor = Cursor(self.connection)
            for texas_land_survey_system in texas_land_survey_system_list:
                if not texas_land_survey_system.county:
                    raise ValueError("Texas Land Survy System county cannot be null")
                try:
                    cursor.execute(
                        AFEDB.SQL.INSERT_TEXAS_LAND_SURVEY_SYSTEM.value,
                        (
                            texas_land_survey_system.county,
                            texas_land_survey_system.fips_code,
                            texas_land_survey_system.abstract,
                            texas_land_survey_system.block,
                            texas_land_survey_system.section,
                            texas_land_survey_system.grantee,
                            texas_land_survey_system.southwest_latitude,
                            texas_land_survey_system.southwest_longitude,
                            texas_land_survey_system.northwest_latitude,
                            texas_land_survey_system.northwest_longitude,
                            texas_land_survey_system.southeast_latitude,
                            texas_land_survey_system.southeast_longitude,
                            texas_land_survey_system.northeast_latitude,
                            texas_land_survey_system.northeast_longitude
                        ),
                    )
                except IntegrityError as e:
                    raise e
            self.connection.commit()  
        except IntegrityError as e:
            self.connection.rollback()
            raise ValueError(f"Unable to insert Texas Land Survey System into database: {e}")
        finally:
            cursor.close()
    
    def get_by_county_abstract(self, county: str, abstract:str) -> TexasLandSurveySystem:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_TEXAS_LAND_SURVEY_SYSTEM_BY_COUNTY_ABSTRACT.value, (county, abstract))
            row = cursor.fetchone()
            if row:
                return TexasLandSurveySystem(*row)
        except DatabaseError as e:
            raise ValueError(f"Unable to get texas land survey system by {county} {abstract}: {e}")
        finally:
            cursor.close()

    def get_by_county_abstract_block_section(self, county: str, abstract:str, block: str, section: str) -> TexasLandSurveySystem:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_TEXAS_LAND_SURVEY_SYSTEM_BY_COUNTY_ABSTRACT_BLOCK_SECTION.value, (county, abstract, block, section))
            row = cursor.fetchone()
            if row:
                return TexasLandSurveySystem(*row)
        except DatabaseError as e:
            raise ValueError(f"Unable to get texas land survey system by {county} {block} {section}: {e}")
        finally:
            cursor.close()

    def get_distinct_counties(self) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_TEXAS_LAND_SURVEY_SYSTEM_DISTINCT_COUNTIES.value)
            return [row[0] for row in cursor.fetchall()]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct counties from Texas Land Survey System: {e}")
        finally:
            cursor.close()

    def get_distinct_abstract_by_county(self, county: str) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_TEXAS_LAND_SURVEY_SYSTEM_DISTINCT_ABSTRACTS_BY_COUNTY.value, (county,))
            return [row[0] for row in cursor.fetchall()]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct abstract by county {county}: {e}")
        finally:
            cursor.close()
        
    def get_distinct_block_by_county_abstract(self, county: str, abstract: str) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_TEXAS_LAND_SURVEY_SYSTEM_DISTINCT_BLOCK_BY_COUNTY_ASTRACT.value, (county, abstract))
            return [row[0] for row in cursor.fetchall()]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct block by county {county} abstract {abstract}: {e}")
        finally:
            cursor.close()  

    def get_distinct_section_by_county_abstract_block(self, county: str, abstract: str, block: str) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_TEXAS_LAND_SURVEY_SYSTEM_DISTINCT_SECTION_BY_COUNTY_ASTRACT_BLOCK.value, (county, abstract, block))
            return [row[0] for row in cursor.fetchall()]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct section by county {county} abstract {abstract} block {block}: {e}")
        finally:
            cursor.close()

    def get_by_county(self, county: str) -> list[TexasLandSurveySystem]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_TEXAS_LAND_SURVEY_SYSTEM_BY_COUNTY.value, (county,))
            rows = cursor.fetchall()
            return [TexasLandSurveySystem(*row) for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get texas land survey system by county {county}: {e}")
        finally:
            cursor.close()