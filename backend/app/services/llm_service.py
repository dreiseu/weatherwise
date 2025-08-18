"""
LLM Service for WeatherWise
Handles AI text generation for DRRM analysis and recommendations
"""

import openai
import os
import logging
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv

env_path = Path(__file__).parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service using OpenAI API."""

    def __init__(self):
        """Initialize LLM Service."""
        self.api_key = os.getenv('OPENAI_API_KEY')

        if not self.api_key:
            logger.warning("OPENAI_API_KEY not found. LLM features will be limited.")
        else:
            openai.api_key = self.api_key
            logger.info("LLM service initialized with OpenAI")

    def generate_drrm_analysis(self, weather_data: Dict, context_docs: List[str]) -> str:
        """Generate DRRM analysis based on weather data and context."""
        
        if not self.api_key:
            return "LLM service not available - missing API key"
        
        # Create prompt for DRRM analysis
        prompt = self._create_drrm_prompt(weather_data, context_docs)
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a Philippine DRRM expert providing disaster risk analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            analysis = response.choices[0].message.content.strip()
            logger.info("Generated DRRM analysis successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Analysis generation failed: {str(e)}"
        
    def _create_drrm_prompt(self, weather_data: Dict, context_docs: List[str]) -> str:
        """Create prompt for DRRM analysis."""
        
        prompt = f"""
        Based on the following weather conditions and DRRM knowledge, provide a disaster risk analysis:

        CURRENT WEATHER:
        - Location: {weather_data.get('location', 'Unknown')}
        - Temperature: {weather_data.get('temperature', 'N/A')}°C
        - Humidity: {weather_data.get('humidity', 'N/A')}%
        - Wind Speed: {weather_data.get('wind_speed', 'N/A')} km/h
        - Pressure: {weather_data.get('pressure', 'N/A')} hPa
        - Condition: {weather_data.get('weather_condition', 'N/A')}

        RELEVANT DRRM KNOWLEDGE:
        """
        
        for i, doc in enumerate(context_docs, 1):
            prompt += f"\n{i}. {doc}\n"
        
        prompt += """
        Please provide:
        1. Risk assessment for the current conditions
        2. Specific recommendations for Philippine DRRM
        3. Any immediate actions needed

        Keep the response concise and actionable.
        """
        
        return prompt

if __name__ == "__main__":
    # Test the service
    llm_service = LLMService()
    print("✅ LLM service created!")