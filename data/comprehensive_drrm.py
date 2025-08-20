"""
Comprehensive Philippine DRRM Knowledge Base
Detailed disaster management protocols and procedures
"""

COMPREHENSIVE_DRRM_DOCS = [
    {
        "id": "ndrrmp_framework",
        "text": """The National Disaster Risk Reduction and Management Plan (NDRRMP) 2020-2030 establishes the framework for disaster risk reduction in the Philippines. The plan operates on four thematic pillars: Prevention and Mitigation, Preparedness, Response, and Rehabilitation and Recovery. Prevention and mitigation focus on reducing vulnerability through hazard mapping, early warning systems, and structural measures. Preparedness involves capacity building, contingency planning, and resource mobilization. Response includes immediate search and rescue, emergency relief, and damage assessment. Rehabilitation and recovery encompass restoration of services, livelihood support, and building back better principles.""",
        "metadata": {"type": "framework", "source": "NDRRMC", "category": "policy", "level": "national"}
    },
    {
        "id": "typhoon_response_protocol",
        "text": """Typhoon response protocol begins with PAGASA issuing tropical cyclone warnings 36-72 hours before landfall. Local Disaster Risk Reduction and Management Offices (LDRRMOs) activate emergency operations centers when Signal No. 1 is declared. Forced evacuation of coastal and landslide-prone areas occurs at Signal No. 3. All residents in storm surge areas must evacuate regardless of signal strength if surge warnings are issued. Emergency supplies include 72-hour food and water reserves, flashlights, batteries, first aid kits, and important documents in waterproof containers. Transportation services suspend operations at Signal No. 3 in affected areas.""",
        "metadata": {"type": "typhoon", "source": "NDRRMC", "category": "response_protocol", "level": "operational"}
    },
    {
        "id": "flood_management_metro_manila",
        "text": """Metro Manila flood management involves coordinated response between MMDA, LGUs, and national agencies. Critical flood-prone areas include Marikina River basin, Pasig River system, Laguna Lake shores, and West Valley fault areas. Flood monitoring stations provide real-time water level data. Pre-emptive evacuation begins when rivers reach first alarm level. Citizens should evacuate when floodwater reaches knee-deep level. Major evacuation centers include covered courts, schools, and barangay halls. Essential services priority: medical emergencies, pregnant women, children, elderly, and persons with disabilities. Rescue operations use rubber boats, amphibious vehicles, and helicopters for isolated areas.""",
        "metadata": {"type": "flooding", "location": "Metro Manila", "category": "management_protocol", "level": "regional"}
    },
    {
        "id": "earthquake_preparedness_guidelines",
        "text": """Earthquake preparedness in the Philippines follows the Drop, Cover, and Hold protocol during shaking. Buildings constructed before 1992 require seismic evaluation due to outdated building codes. Tsunami evacuation zones extend 2 kilometers inland from coastlines with elevation below 10 meters. Emergency kits should include hard hats, sturdy shoes, emergency radio, and evacuation route maps. Post-earthquake procedures involve checking for gas leaks, structural damage, and injuries before evacuating if necessary. Aftershock precautions continue for weeks following major earthquakes. Critical infrastructure inspection covers bridges, hospitals, schools, and government buildings.""",
        "metadata": {"type": "earthquake", "source": "PHIVOLCS", "category": "preparedness", "level": "national"}
    },
    {
        "id": "volcanic_eruption_response",
        "text": """Volcanic eruption response varies by alert level established by PHIVOLCS. Alert Level 0 indicates normal conditions with background monitoring. Alert Level 1 shows abnormal volcanic activity requiring increased monitoring. Alert Level 2 indicates probable magmatic eruption with evacuation of 6km danger zone. Alert Level 3 signals magmatic eruption in progress with evacuation of 7km radius. Alert Level 4 represents hazardous explosive eruption imminent with evacuation of 8km extended danger zone. Ashfall protection requires N95 masks, eye protection, and covered water sources. Livestock and agriculture protection includes sheltering animals and covering crops.""",
        "metadata": {"type": "volcanic", "source": "PHIVOLCS", "category": "alert_system", "level": "technical"}
    }
]