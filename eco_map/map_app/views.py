from django.shortcuts import render
from xml.dom.minidom import parseString
import os
from pathlib import Path

def home(request):
    return render(request, 'map_app/index.html')

def get_region_name(region_id):
    svg_path = os.path.join(Path(__file__).parent, 'static', 'map_app', 'russia.svg')
    try:
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()
        dom = parseString(svg_content)
        for path in dom.getElementsByTagName('path'):
            if path.getAttribute('id') == region_id:
                title = path.getAttribute('title')
                return title        
    except Exception as e:
        raise e

def ml_analysis(request):
    region_id = request.GET.get('region_id', '')
    region_name = get_region_name(region_id)

    fire_types = [
        'Природный пожар',  
        'Лесной пожар',
        'Контролируемый пал',
        'Неконтролируемый пал',
        'Торфяной пожар',
    ]
    return render(request, 'map_app/ml_analysis.html', {
        'region_id': region_id,
        'region_name': region_name,
        'fire_types': fire_types,
    })
