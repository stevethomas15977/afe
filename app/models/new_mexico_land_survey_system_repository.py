from sqlite3 import Connection, Cursor, DatabaseError, IntegrityError

from database import AFEDB
from models import NewMexicoLandSurveySystem


class NewMexicoLandSurveySystemRepository:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = Connection(db_path)

    def __del__(self):
        self.connection.close()
    
    def get_by_county_township_range_section(self, county:str, township: int, township_direction: str, range:int, range_direction: str, section: str) -> NewMexicoLandSurveySystem:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_BY_COUNTY_TOWNSHIP_RANGE_SECTION.value, (county, township, township_direction, range, range_direction, section,))
            row = cursor.fetchone()
            if row:
                return NewMexicoLandSurveySystem(*row)
        except DatabaseError as e:
            raise ValueError(f"Unable to get new mexico land survey system by {township} {township_direction} {range} {range_direction} {section}: {e}")
        finally:
            cursor.close()

    def get_distinct_counties(self) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_DISTINCT_COUNTIES.value)
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct counties from new mexico land survey system: {e}")
        finally:
            cursor.close()

    def get_distinct_townships_by_county(self, county: str) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_DISTINCT_TOWNSHIPS_BY_COUNTY.value, (county,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct abstract by county {county} from new mexico land survey system: {e}")
        finally:
            cursor.close()

    def get_distinct_township_directions_by_county_township(self, county: str, township: str) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_DISTINCT_TOWNSHIP_DIRECTIONS_BY_COUNTY_TOWNSHIP.value, (county, township,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct township directions by county {county} and township {township} from new mexico land survey system: {e}")
        finally:
            cursor.close()
            
    def get_distinct_ranges_by_county_township_range(self, county: str, township: str, township_direction: str) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_DISTINCT_RANGE_BY_COUTY_TOWNSHIP_TOWNSHIP_DIRECTION.value, (county, township, township_direction,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct range directions by county {county} and township {township} and township direction {township_direction} from new mexico land survey system: {e}")
        finally:
            cursor.close()
    def get_distinct_range_directions_by_county_township_township_direction_range(self, county: str, township: str, township_direction: str, range: int) -> list[str]:  
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_DISTINCT_RANGE_DIRECTIONS_BY_COUTY_TOWNSHIP_TOWNSHIP_DIRECTION_RANGE.value, (county, township, township_direction, range,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct range directions by county {county} and township {township} and township direction {township_direction} and range {range} from new mexico land survey system: {e}")
        finally:
            cursor.close()

    def get_distinct_sections_by_county_township_township_direction_range_range_direction(self, county: str, township: str, township_direction: str, range: int, range_direction: str) -> list[str]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_DISTINCT_SECTIONS_BY_COUNTY_TOWNSHIP_TOWNSHIP_DIRECTION_RANGE_RANGE_DIRECTION.value, (county, township, township_direction, range, range_direction,))
            rows = cursor.fetchall()
            return [row[0] for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get distinct sections by county {county} and township {township} and township direction {township_direction} and range {range} and range direction {range_direction} from new mexico land survey system: {e}")
        finally:
            cursor.close()  

    def get(self, county: str, township: str, township_direction: str, range: str, range_direction: str, section: str) -> NewMexicoLandSurveySystem:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM.value, (county, township, township_direction, range, range_direction, section,))
            row = cursor.fetchone()
            if row:
                return NewMexicoLandSurveySystem(*row)
        except DatabaseError as e:
            raise ValueError(f"Unable to get new mexico land survey system by {township} {township_direction} {range} {range_direction} {section}: {e}")
        finally:
            cursor.close()
            
    def get_by_county(self, county: str) -> list[NewMexicoLandSurveySystem]:
        try:
            cursor = Cursor(self.connection)
            cursor.execute(AFEDB.SQL.SELECT_NEW_MEXICO_LAND_SURVEY_SYSTEM_BY_COUNTY.value, (county,))
            rows = cursor.fetchall()
            return [NewMexicoLandSurveySystem(*row) for row in rows]
        except DatabaseError as e:
            raise ValueError(f"Unable to get new mexico land survey system by county {county}: {e}")
        finally:
            cursor.close()

 