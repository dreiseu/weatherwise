"""
Philippine DRRM Knowledge Base
Contains protocols, procedures, and guidelines for disaster management
"""

DRRM_DOCUMENTS = [
    {
        "id": "pagasa_typhoon_signals",
        "text": "PAGASA Typhoon Warning Signals: Signal No. 1 (39-61 km/h winds in 36 hours), Signal No. 2 (62-88 km/h in 24 hours), Signal No. 3 (89-117 km/h in 18 hours), Signal No. 4 (118-184 km/h in 12 hours), Signal No. 5 (above 185 km/h in 12 hours).",
        "metadata": {"type": "typhoon", "source": "PAGASA", "category": "warning_signals"}
    },
    {
        "id": "metro_manila_evacuation",
        "text": "Metro Manila evacuation procedures: Residents in flood-prone areas like Marikina, Pasig riverbanks, and Laguna Lake shores should evacuate when water reaches knee-deep levels. Evacuation centers are located in schools and barangay halls.",
        "metadata": {"type": "flooding", "location": "Metro Manila", "category": "evacuation"}
    },
    {
        "id": "ndrrmc_structure",
        "text": "NDRRMC (National Disaster Risk Reduction and Management Council) leads disaster response coordination. LGUs implement local disaster plans. LDRRMC coordinates at city/municipal level. Barangay DRRMCs handle community-level response.",
        "metadata": {"type": "general", "source": "NDRRMC", "category": "organization"}
    },
    {
        "id": "heat_index_warnings",
        "text": "Heat Index warnings in the Philippines: 27-32°C (Caution), 33-39°C (Extreme Caution), 40-51°C (Danger), above 52°C (Extreme Danger). PAGASA issues heat advisories when temperatures reach dangerous levels.",
        "metadata": {"type": "heat", "source": "PAGASA", "category": "health_warnings"}
    },
    {
        "id": "flash_flood_guidelines",
        "text": "Flash flood safety: Never walk through flowing water. 15cm can knock you down, 60cm can sweep away vehicles. Move to higher ground immediately. Monitor PAGASA flood bulletins and local warnings.",
        "metadata": {"type": "flooding", "source": "NDRRMC", "category": "safety_guidelines"}
    },
    {
        "id": "landslide_risk_areas",
        "text": "Landslide-prone areas include mountainous regions in Northern Luzon, Cordillera, and Eastern Visayas. Watch for warning signs: ground cracks, tilting trees, muddy water in streams, and unusual sounds from slopes.",
        "metadata": {"type": "landslide", "location": "Philippines", "category": "risk_assessment"}
    },
    {
        "id": "storm_surge_zones",
        "text": "Storm surge affects coastal areas especially in Eastern Visayas, Bicol, and Eastern Luzon facing the Pacific. Surge height can reach 3-6 meters during strong typhoons. Evacuate coastal communities when typhoon signal 3 is raised.",
        "metadata": {"type": "storm_surge", "location": "Coastal Philippines", "category": "evacuation"}
    }
]