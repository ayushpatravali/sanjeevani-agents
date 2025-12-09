
import sys
import os
import plotly.graph_objects as go

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from src.tools import map_utils

def test_map_generation():
    print("Testing Map Generation...")
    
    # Sample districts
    test_districts = ["Bagalkot", "Bellary", "Mysore", "UnknownDistrict"]
    
    try:
        fig = map_utils.generate_karnataka_map(test_districts)
        
        if fig is None:
            print("❌ Failed: Figure is None (GeoJSON might be missing)")
            return
            
        if not isinstance(fig, go.Figure):
            print(f"❌ Failed: Returned object is not a Plotly Figure, got {type(fig)}")
            return
            
        print("✅ Success: Plotly Figure generated!")
        print(f"Data points in plot: {len(fig.data[0].locations)}")
        
        # Optional: Save validation image or html if execution environment supported it, 
        # but for now we just verify object creation.
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_map_generation()
