import json
import os
import sqlite3

counties = ['lea', 'eddy', 'chaves', 'roosevelt', 'curry', 'de_baca', 'quay', 'harding', 'san_miguel', 'mora', 'guadalupe', 'torrance', 'lincoln', 'otero', 'sierra', 'socorro', 'valencia', 'santa_fe', 'sandoval', 'rio_arriba', 'los_alamos', 'taos', 'colfax', 'union', 'san_juan', 'mckinley', 'santa_fe', 'rio_arriba', 'sandoval', 'bernalillo', 'valencia', 'torrance']
base_path = '/home/ubuntu/afe/geojson/new_mexico/states'

def find_corners(coordinates: list) -> dict:
    # Initialize variables to store min and max latitudes and longitudes
    min_lat = float('inf')
    max_lat = float('-inf')
    min_lon = float('inf')
    max_lon = float('-inf')

    # Handle "Polygon" or "MultiPolygon" coordinates
    if isinstance(coordinates[0][0][0], list):
        # MultiPolygon case: Iterate through all polygons and their points
        for polygon in coordinates:
            for ring in polygon:  # Iterate over each ring of the polygon
                for lon, lat in ring:  # Loop through each coordinate pair
                    min_lat = min(min_lat, lat)
                    max_lat = max(max_lat, lat)
                    min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
    else:
        # Polygon case: Directly iterate through the single polygon's points
        for lon, lat in coordinates[0]:  # Loop through the coordinates
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)

    # Define the corners using the min and max values found
    southwest_corner = (min_lat, min_lon)
    southeast_corner = (min_lat, max_lon)
    northwest_corner = (max_lat, min_lon)
    northeast_corner = (max_lat, max_lon)

    # Return the corners as a dictionary
    return {
        "southwest_corner": southwest_corner,
        "southeast_corner": southeast_corner,
        "northwest_corner": northwest_corner,
        "northeast_corner": northeast_corner
    }

insert_command = '''
        INSERT INTO new_mexico_land_survey_system (
        county,
        township,
        township_direction,
        range, 
        range_direction,
        section,
        southwest_latitude,
        southwest_longitude,
        northwest_latitude,
        northwest_longitude,
        southeast_latitude,
        southeast_longitude,
        northeast_latitude,
        northeast_longitude
        ) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT DO NOTHING
    '''

create_table_command = '''
        CREATE TABLE IF NOT EXISTS new_mexico_land_survey_system (
            county TEXT,
            township INEGER,
            township_direction TEXT,
            range INTEGER,
            range_direction TEXT,
            section INTEGER,
            southwest_latitude REAL,
            southwest_longitude REAL,
            northwest_latitude REAL,
            northwest_longitude REAL,
            southeast_latitude REAL,
            southeast_longitude REAL,
            northeast_latitude REAL,
            northeast_longitude REAL
        )
    '''
def create_table_in_db(db_path, table_ddl):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS new_mexico_land_survey_system")
        cursor.execute(table_ddl)
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

def insert_into_db(db_path, table_dml, rows):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.executemany(table_dml, rows)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        conn.close()

def main():
    try:
        db_path = os.path.join(base_path, "new_mexico_land_survey_system.db")
        create_table_in_db(db_path=db_path, table_ddl=create_table_command)
        for county in counties:
            directory_path = os.path.join(base_path, county)
            if not os.path.exists(directory_path):
                continue
            print(f"Creating {county} from {directory_path}")

            for file in os.listdir(directory_path):
                filename = os.fsdecode(file)
                rows_to_insert = []
                print(filename)
                with open(os.path.join(directory_path, filename)) as f:
                    data = json.load(f)
                    for feature in data['features']:
                        FRSTDIVID = list(feature['properties']['FRSTDIVID'])
                        if len(FRSTDIVID) < 19:
                            continue
                        # print(f" {feature['properties']['FRSTDIVID']}")
                        township = int(f"{FRSTDIVID[5]}{FRSTDIVID[6]}".lstrip('0'))
                        township_direction = FRSTDIVID[8]
                        range = int(f"{FRSTDIVID[10]}{FRSTDIVID[11]}".lstrip('0'))
                        range_direction = FRSTDIVID[13]
                        section = f"{FRSTDIVID[17]}{FRSTDIVID[18]}".lstrip('0')
                        # print(f" {township}-{range}-{section}")
                        corners = find_corners(coordinates=feature['geometry']['coordinates'])
                        if not corners:
                            continue
                        # print(f" Southwest corner - {corners['southwest_corner']}")
                        row = [
                                county,
                                township, 
                                township_direction,
                                range, 
                                range_direction,
                                section,
                                corners['southwest_corner'][0], 
                                corners['southwest_corner'][1], 
                                corners['northwest_corner'][0], 
                                corners['northwest_corner'][1], 
                                corners['southeast_corner'][0], 
                                corners['southeast_corner'][1], 
                                corners['northeast_corner'][0], 
                                corners['northeast_corner'][1]
                            ]
                        rows_to_insert.append(row)
                insert_into_db(db_path=db_path, table_dml=insert_command, rows=rows_to_insert)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    main()