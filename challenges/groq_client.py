import os
import json
import aiohttp
from typing import Optional, Dict, Any

class GroqClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.1-8b-instant"  # Fast and free model
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
    
    async def parse_team_registration(self, input_text: str) -> Dict[str, Optional[str]]:
        """
        Parse team registration input using AI to extract team name and server link
        Handles various input formats and orders
        """
        prompt = f"""
You are a team registration parser. Extract the team name and server link from the input text.

Rules:
1. Team name: Any text that appears to be a team/group name (can contain spaces, numbers, symbols)
2. Server link: Any URL (starts with http/https or contains facebook.com, discord.gg, etc.)
3. Ignore common words like "PC", "TEAM", "GUILD" unless they're clearly part of the team name
4. If there are multiple words that could be a team name, combine them intelligently

Input: "{input_text}"

Respond with ONLY a JSON object in this format:
{{"team_name": "extracted team name or null", "server_link": "extracted URL or null"}}

Examples:
- "UNKNOWN PC https://www.facebook.com/mrakuji/" → {{"team_name": "UNKNOWN PC", "server_link": "https://www.facebook.com/mrakuji/"}}
- "https://www.facebook.com/mrakuji/ UNKNOWN 50 PC" → {{"team_name": "UNKNOWN 50 PC", "server_link": "https://www.facebook.com/mrakuji/"}}
- "Team Alpha discord.gg/xyz123" → {{"team_name": "Team Alpha", "server_link": "discord.gg/xyz123"}}
- "Warriors" → {{"team_name": "Warriors", "server_link": null}}
"""

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,  # Low temperature for consistent parsing
                    "max_tokens": 150
                }
                
                async with session.post(self.base_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content'].strip()
                        
                        # Try to parse JSON response
                        try:
                            parsed = json.loads(content)
                            return {
                                'team_name': parsed.get('team_name'),
                                'server_link': parsed.get('server_link')
                            }
                        except json.JSONDecodeError:
                            # Fallback: manual parsing if AI doesn't return valid JSON
                            return self._fallback_parse(input_text)
                    else:
                        print(f"Groq API error: {response.status}")
                        return self._fallback_parse(input_text)
                        
        except Exception as e:
            print(f"Error calling Groq API: {e}")
            return self._fallback_parse(input_text)
    
    def _fallback_parse(self, input_text: str) -> Dict[str, Optional[str]]:
        """
        Fallback parsing method if AI fails
        Simple regex-based parsing
        """
        import re
        
        # Extract URL
        url_pattern = r'https?://[^\s]+|(?:www\.)?(?:facebook|discord|twitter|instagram)\.(?:com|gg)/[^\s]+'
        url_match = re.search(url_pattern, input_text, re.IGNORECASE)
        server_link = url_match.group(0) if url_match else None
        
        # Extract team name (everything except the URL)
        if server_link:
            team_name = input_text.replace(server_link, '').strip()
        else:
            team_name = input_text.strip()
        
        # Clean up team name
        if team_name and len(team_name) > 0:
            team_name = ' '.join(team_name.split())  # Normalize whitespace
        else:
            team_name = None
            
        return {
            'team_name': team_name,
            'server_link': server_link
        }
    
    async def generate_response(self, prompt: str, max_tokens: int = 100) -> str:
        """
        General AI response generation for other bot features
        """
        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                data = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": max_tokens
                }
                
                async with session.post(self.base_url, headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result['choices'][0]['message']['content'].strip()
                    else:
                        return "Sorry, I'm having trouble thinking right now. 🤖"
                        
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return "Oops, my brain circuits are a bit tangled! 🤖⚡"
    
    async def generate_duplicate_team_message(self, team_name: str, guild_name: str, existing_user_name: str = None) -> str:
        """
        Generate a friendly AI response for duplicate team name situations
        """
        if existing_user_name:
            prompt = f"""
Generate a friendly Discord bot message telling a user that the team name "{team_name}" is already taken by {existing_user_name} in the server "{guild_name}". 

Be helpful and suggest alternatives like:
- Adding a number (Team Alpha 2)
- Adding their username
- Using similar names
- Being creative with the name

Keep it concise, friendly, and helpful. Use emojis appropriately. Start with an appropriate emoji and mention the conflict clearly.
"""
        else:
            prompt = f"""
Generate a friendly Discord bot message telling a user that the team name "{team_name}" is already registered in the server "{guild_name}".

Be helpful and suggest alternatives like:
- Adding a number (Team Alpha 2) 
- Using creative variations
- Adding descriptive words

Keep it concise, friendly, and helpful. Use emojis appropriately. Start with an appropriate emoji.
"""
        
        try:
            response = await self.generate_response(prompt, max_tokens=150)
            return response
        except Exception as e:
            # Fallback message if AI fails
            if existing_user_name:
                return f"⚠️ Team name **{team_name}** is already taken by **{existing_user_name}** in this server!\nTry: `{team_name} 2`, `{team_name} Elite`, or be creative! 🎯"
            else:
                return f"⚠️ Team name **{team_name}** is already registered in this server!\nTry adding a number or variation like `{team_name} 2` or `{team_name} Pro`! 🎯"
    
    async def detect_challenge_category(self, team_name: str, server_link: str = None) -> dict:
        """
        Use AI to detect which challenge category a team belongs to based on team name and server link
        Returns dict with 'category_id' (1-5) and 'confidence' ('high'/'low')
        """
        categories = [
            "1. Clash Squad Limited - Limited clash squad matches with restricted loadouts",
            "2. Clash Squad Unlimited - Unlimited clash squad matches with full access to weapons", 
            "3. Clash Squad Quantra - Quantra-based clash squad battles",
            "4. Full Map - Full battle royale map games",
            "5. Custom - Custom game modes and challenges"
        ]
        
        prompt = f"""
You are an expert Free Fire game mode classifier. Based on the team name and optional server link, determine which category this team belongs to and your confidence level.

Team Name: "{team_name}"
Server Link: "{server_link or 'Not provided'}"

Available Categories:
{chr(10).join(categories)}

Rules for classification:
- HIGH CONFIDENCE: Clear keywords like "CS Limited", "CS Unlimited", "Quantra", "BR", "Full Map"
- LOW CONFIDENCE: Vague names, unclear indicators, or mixed terms

Respond with ONLY: [category_number] [confidence_level]

Examples:
- "CS Limited Warriors" → 1 high
- "cs limited" → 1 high
- "Unlimited Squad" → 2 high
- "Quantra Legends" → 3 high
- "BR Champions" → 4 high
- "Gaming Squad" → 5 low
- "Elite Team" → 5 low
"""

        try:
            response = await self.generate_response(prompt, max_tokens=15)
            # Extract category number and confidence level
            import re
            match = re.search(r'([1-5])\s+(high|low)', response.lower())
            if match:
                category_id = int(match.group(1))
                confidence = match.group(2)
                return {
                    'category_id': category_id,
                    'confidence': confidence
                }
            else:
                # Fallback: just look for number
                number_match = re.search(r'[1-5]', response)
                if number_match:
                    return {
                        'category_id': int(number_match.group()),
                        'confidence': 'low'
                    }
                else:
                    return {
                        'category_id': 5,
                        'confidence': 'low'
                    }
        except Exception as e:
            print(f"Error detecting category: {e}")
            return {
                'category_id': 5,
                'confidence': 'low'
            }
    
    async def suggest_category_with_prompt(self, team_name: str, server_link: str = None) -> str:
        """
        Generate an AI-powered category suggestion prompt for the user
        """
        categories = [
            "1. Clash Squad Limited - Limited clash squad matches with restricted loadouts",
            "2. Clash Squad Unlimited - Unlimited clash squad matches with full access to weapons", 
            "3. Clash Squad Quantra - Quantra-based clash squad battles",
            "4. Full Map - Full battle royale map games",
            "5. Custom - Custom game modes and challenges"
        ]
        
        prompt = f"""
Based on the team name "{team_name}", suggest which Free Fire challenge category this team most likely belongs to.

Available Categories:
{chr(10).join(categories)}

Create a helpful response that:
1. Suggests the most likely category with reasoning
2. Shows all 5 categories with numbers for selection
3. Asks the user to reply with the category number
4. Is friendly and encouraging

Keep it concise but informative. Use emojis appropriately.
"""

        try:
            response = await self.generate_response(prompt, max_tokens=200)
            return response
        except Exception as e:
            print(f"Error generating category suggestion: {e}")
            # Fallback message
            return f"""🎯 **Please select a category for your team "{team_name}":**

1️⃣ **Clash Squad Limited** - Limited loadouts
2️⃣ **Clash Squad Unlimited** - Full weapon access  
3️⃣ **Clash Squad Quantra** - Quantra battles
4️⃣ **Full Map** - Battle Royale games
5️⃣ **Custom** - Custom game modes

Reply with `!entry [team name] [category number]` (e.g., `!entry {team_name} 2`)"""