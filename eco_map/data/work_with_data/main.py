import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
import json
import os

gpkg_path = "../raw_data/geoRus/gadm41_RUS.gpkg"
fire_path = "../raw_data/Fire/Fire.csv"
regions_layer = "ADM_ADM_2"
output_path = "../regions_fire"
os.makedirs("../regions_fire", exist_ok=True)


region_to_code = {
    'Adygey': 'RU-AD',
    'Altay': 'RU-ALT',  # Алтайский край
    'Amur': 'RU-AMU',
    "Arkhangel'sk": 'RU-ARK',
    "Astrakhan'": 'RU-AST',
    'Bashkortostan': 'RU-BA',
    'Belgorod': 'RU-BEL',
    'Bryansk': 'RU-BRY',
    'Buryat': 'RU-BU',
    'Chechnya': 'RU-CE',
    'Chelyabinsk': 'RU-CHE',
    'Chukot': 'RU-CHU',  
    'Chuvash': 'RU-CU',
    'City of St. Petersburg': 'RU-SPE',
    'Dagestan': 'RU-DA',
    'Gorno-Altay': 'RU-RAL',  # Республика Алтай
    'Ingush': 'RU-IN',
    'Irkutsk': 'RU-IRK',
    'Ivanovo': 'RU-IVA',
    'Kabardin-Balkar': 'RU-KB',
    'Kaliningrad': 'RU-KGD',
    'Kalmyk': 'RU-KL',
    'Kaluga': 'RU-KLU',
    'Kamchatka': 'RU-KAM',
    'Karachay-Cherkess': 'RU-KC',
    'Karelia': 'RU-KR',
    'Kemerovo': 'RU-KEM',
    'Khabarovsk': 'RU-KHA',
    'Khakass': 'RU-KK',
    'Khanty-Mansiy': 'RU-KHM',
    'Kirov': 'RU-KIR',
    'Komi': 'RU-KO',
    'Kostroma': 'RU-KOS',
    'Krasnodar': 'RU-KDA',
    'Krasnoyarsk': 'RU-KYA',
    'Kurgan': 'RU-KGN',
    'Kursk': 'RU-KRS',
    'Leningrad': 'RU-LEN',
    'Lipetsk': 'RU-LIP',
    'Magadan': 'RU-MAG',
    'Mariy-El': 'RU-ME',
    'Mordovia': 'RU-MO',
    'Moscow City': 'RU-MOW',  # город Москва
    'Moskva': 'RU-MOS',  # Московская область
    'Murmansk': 'RU-MUR',
    'Nenets': 'RU-NEN',
    'Nizhegorod': 'RU-NIZ',
    'North Ossetia': 'RU-SE',
    'Novgorod': 'RU-NGR',
    'Novosibirsk': 'RU-NVS',
    'Omsk': 'RU-OMS',
    'Orel': 'RU-ORL',
    'Orenburg': 'RU-ORE',
    'Penza': 'RU-PNZ',
    "Perm'": 'RU-PER',
    "Primor'ye": 'RU-PRI',
    'Pskov': 'RU-PSK',
    'Rostov': 'RU-ROS',
    'Ryazan': 'RU-RYA',
    'Sakha': 'RU-SA',
    'Sakhalin': 'RU-SAK',
    'Samara': 'RU-SAM',
    'Saratov': 'RU-SAR',
    'Smolensk': 'RU-SMO',
    "Stavropol'": 'RU-STA',
    'Sverdlovsk': 'RU-SVE',
    'Tambov': 'RU-TAM',
    'Tatarstan': 'RU-TA',
    'Tomsk': 'RU-TOM',
    'Tula': 'RU-TUL',
    'Tuva': 'RU-TY',
    "Tver'": 'RU-TVE',  # Возможная путаница с кавычками
    "Tyumen'": 'RU-TYU',  # Возможная путаница с кавычками
    'Udmurt': 'RU-UD',
    "Ul'yanovsk": 'RU-ULY',  # Возможная путаница с кавычками
    'Vladimir': 'RU-VLA',
    'Volgograd': 'RU-VGG',
    'Vologda': 'RU-VLG',
    'Voronezh': 'RU-VOR',
    'Yamal-Nenets': 'RU-YAN',
    "Yaroslavl'": 'RU-YAR',  # Возможная путаница с кавычками
    'Yevrey': 'RU-YEV',
    "Zabaykal'ye": 'RU-ZAB'
}


regions_gdf = gpd.read_file(gpkg_path, layer=regions_layer).to_crs("EPSG:4326")
print(regions_gdf['NAME_1'].unique())
regions_gdf = regions_gdf[['NAME_1', 'geometry']]
regions_sindex = regions_gdf.sindex

region_names = regions_gdf['NAME_1'].unique().tolist()


def find_region(lon: float, lat: float) -> str:
    """Возвращает название района или None"""
    try:
        point = Point(lon, lat)
        possible_matches = list(regions_sindex.intersection(point.bounds))
        for idx in possible_matches:
            if regions_gdf.iloc[idx].geometry.contains(point):
                return regions_gdf.iloc[idx]['NAME_1']
        return None
    except:
        return None

# chunksize = 50000
# fire_types = ['Природный пожар', 'Лесной пожар', 'Контролируемый пал', 'Неконтролируемый пал', 'Торфяной пожар']
# cnt = 1
# with pd.read_csv(fire_path, sep=';', chunksize=chunksize) as reader:
#     for chunk in reader:
#         cnt += 1
#         valid_chunk = chunk.dropna(subset=['lon', 'lat'])

#         region_buffer = {}

#         for x, row in valid_chunk.iterrows():
#             region_name = find_region(row['lon'], row['lat'])
#             fire_type = str(row['type_name']).strip()
#             fire_date = row['dt']

#             if region_name and fire_type in fire_types:
#                 region_code = region_to_code.get(region_name)
#                 if region_code:
#                     if region_code not in region_buffer:
#                         region_buffer[region_code] = {"fire_stats": {"total": 0, **{t: 0 for t in fire_types}}, "fires": {t: [] for t in fire_types}}

#                     region_buffer[region_code]["fire_stats"]["total"] += 1
#                     region_buffer[region_code]["fire_stats"][fire_type] += 1
#                     region_buffer[region_code]["fires"][fire_type].append(fire_date)

#         for region_code, buffer_data in region_buffer.items():
#             region_file_path = os.path.join(output_path, f"{region_code}.json")

#             if os.path.exists(region_file_path):
#                 with open(region_file_path, 'r', encoding='utf-8') as f:
#                     existing_data = json.load(f)
#             else:
#                 existing_data = {"fire_stats": {"total": 0, **{t: 0 for t in fire_types}}, "fires": {t: [] for t in fire_types}}

#             # Объединяем
#             for fire_type in fire_types:
#                 existing_data["fire_stats"][fire_type] += buffer_data["fire_stats"][fire_type]
#                 existing_data["fires"][fire_type].extend(buffer_data["fires"][fire_type])
#             existing_data["fire_stats"]["total"] += buffer_data["fire_stats"]["total"]

#             with open(region_file_path, 'w', encoding='utf-8') as f:
#                 json.dump(existing_data, f, ensure_ascii=False, indent=4)
                    