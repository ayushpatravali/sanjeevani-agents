import json
import os
import plotly.express as px
import pandas as pd
from rapidfuzz import process

# Load GeoJSON once
GEOJSON_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "karnataka_districts.geojson")

def load_geojson():
    if not os.path.exists(GEOJSON_PATH):
        return None
    with open(GEOJSON_PATH, 'r') as f:
        return json.load(f)

def generate_karnataka_map(highlight_districts):
    """
    Generates a Plotly Choropleth map of Karnataka with specific districts highlighted.
    
    Args:
        highlight_districts (list): List of district names to highlight (e.g., ["Bagalkot", "Mysore"])
    
    Returns:
        plotly.graph_objects.Figure: The map figure
    """
    geojson = load_geojson()
    if not geojson:
        return None

    # Extract all district names from GeoJSON to ensure perfect matching
    # Adjust relevant key based on GeoJSON structure (usually 'district' or 'DISTRICT')
    # From previous observation: properties["district"]
    all_districts = []
    for feature in geojson['features']:
        props = feature['properties']
        # Try common keys
        d_name = props.get('district') or props.get('DISTRICT') or props.get('dtname') or props.get('Name')
        if d_name:
            all_districts.append(d_name)
    
    # Create Data for Plotting
    data = []
    
    # Simple normalization helper
    def normalize(name):
        return name.lower().replace(" ", "").replace("-", "")

    highlight_set = set()
    
    # Fuzzy match input districts to GeoJSON districts
    for input_d in highlight_districts:
        match = process.extractOne(input_d, all_districts, score_cutoff=80)
        if match:
            highlight_set.add(match[0])
            
    for district in all_districts:
        status = "Present" if district in highlight_set else "Absent"
        color_val = 1 if district in highlight_set else 0
        data.append({"District": district, "Status": status, "ColorVal": color_val})
        
    df = pd.DataFrame(data)
    
    # Plot
    fig = px.choropleth(
        df,
        geojson=geojson,
        locations='District',
        featureidkey='properties.district', # Match the key used in GeoJSON
        color='Status',
        color_discrete_map={"Present": "green", "Absent": "lightgrey"},
        hover_data=["District"],
        title="Plant Distribution in Karnataka",
    )
    
    fig.update_geos(fitbounds="locations", visible=False)
    fig.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        showlegend=True
    )
    
    return fig
