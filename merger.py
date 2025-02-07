import discord
from discord import app_commands
import requests
import re
import json
import logging
from typing import List
from bs4 import BeautifulSoup
import asyncio
import shelve
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ds_merger_bot')

# Bot configuration
TOKEN = 'REPLACE_WITH_YOUR_BOT_TOKEN'

# Create data directory if it doesn't exist
DATA_DIR = Path('data')
DATA_DIR.mkdir(exist_ok=True)
DEFAULT_URLS_FILE = DATA_DIR / 'default_urls'

# Initialize bot with intents
intents = discord.Intents.default()
class DSMergerBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        # This copies the global commands over to your guild.
        await self.tree.sync()

client = DSMergerBot()

class DSUltimateError(Exception):
    """Custom exception for DS Ultimate related errors"""
    pass

class UserPreferences:
    """Handles user preference storage and retrieval"""
    
    @staticmethod
    def get_default_url(user_id: int) -> str:
        """Get the default target URL for a user"""
        with shelve.open(str(DEFAULT_URLS_FILE)) as db:
            return db.get(str(user_id))
    
    @staticmethod
    def set_default_url(user_id: int, url: str) -> None:
        """Set the default target URL for a user"""
        with shelve.open(str(DEFAULT_URLS_FILE)) as db:
            db[str(user_id)] = url
    
    @staticmethod
    def remove_default_url(user_id: int) -> bool:
        """Remove the default target URL for a user"""
        with shelve.open(str(DEFAULT_URLS_FILE)) as db:
            try:
                del db[str(user_id)]
                return True
            except KeyError:
                return False

def sanitize_url(url: str) -> str:
    """
    Remove the sensitive key part from the URL for display purposes
    """
    parts = url.split('/')
    parts[-1] = '*' * 8
    return '/'.join(parts)

def validate_ds_ultimate_url(url: str) -> bool:
    """
    Validate if the URL is a valid DS Ultimate attack planner URL
    """
    pattern = r'https://ds-ultimate\.de/tools/attackPlanner/\d+/(?:edit|exportWB|importWB)/[a-zA-Z0-9_-]+'
    return bool(re.match(pattern, url))

def get_plan_key(url: str) -> str:
    """
    Extract the key from the DS Ultimate URL
    """
    return url.split('/')[-1]

def convert_url_to_export(url: str) -> str:
    """
    Convert an edit URL to an export URL
    """
    return url.replace('/edit/', '/exportWB/')

def convert_url_to_import(url: str) -> str:
    """
    Convert an edit URL to an import URL
    """
    return url.replace('/edit/', '/importWB/')

def get_tokens(session: requests.Session, url: str) -> tuple:
    """
    Get CSRF tokens from the edit page
    """
    try:
        response = session.get(url)
        response.raise_for_status()
        
        # Parse the HTML to get the CSRF token
        soup = BeautifulSoup(response.text, 'html.parser')
        meta_token = soup.find('meta', {'name': 'csrf-token'})
        if not meta_token:
            raise DSUltimateError("Could not find CSRF token in page")
        
        csrf_token = meta_token['content']
        
        # Get XSRF token from cookies
        xsrf_token = session.cookies.get('XSRF-TOKEN')
        if not xsrf_token:
            raise DSUltimateError("Could not find XSRF token in cookies")
        
        return csrf_token, xsrf_token
    except requests.RequestException as e:
        logger.error(f"Failed to get tokens: {e}")
        raise DSUltimateError(f"Failed to get authentication tokens: {str(e)}")

async def export_plan(session: requests.Session, url: str) -> str:
    """
    Export plan data from a DS Ultimate URL
    """
    try:
        export_url = convert_url_to_export(url)
        # Get tokens first from the edit page
        csrf_token, xsrf_token = get_tokens(session, url)
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "x-csrf-token": csrf_token,
            "x-xsrf-token": xsrf_token,
            "x-requested-with": "XMLHttpRequest",
        }
        
        response = session.get(export_url, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if 'data' not in data:
            raise DSUltimateError("Invalid export data format")
        
        return data['data']
    
    except requests.RequestException as e:
        logger.error(f"Export request failed: {e}")
        raise DSUltimateError(f"Failed to export plan: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Export JSON parsing failed: {e}")
        raise DSUltimateError("Failed to parse export data")

async def import_plan(session: requests.Session, target_url: str, export_data: str) -> bool:
    """
    Import plan data into a DS Ultimate URL
    """
    try:
        import_url = convert_url_to_import(target_url)
        key = get_plan_key(target_url)
        
        # Get tokens first from the edit page
        csrf_token, xsrf_token = get_tokens(session, target_url)
        
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "x-csrf-token": csrf_token,
            "x-xsrf-token": xsrf_token,
            "x-requested-with": "XMLHttpRequest",
            "referer": target_url
        }
        
        payload = {
            "import": export_data,
            "key": key
        }
        
        response = session.post(import_url, json=payload, headers=headers)
        response.raise_for_status()
        
        return True
    
    except requests.RequestException as e:
        logger.error(f"Import request failed: {e}")
        raise DSUltimateError(f"Failed to import plan: {str(e)}")

@client.event
async def on_ready():
    """
    Event handler for when the bot is ready
    """
    logger.info(f'{client.user} has connected to Discord!')

async def do_merge(interaction: discord.Interaction, target_url: str, source_urls: List[str]):
    """
    Helper function to perform the merge operation
    """
    try:
        # Create a session to maintain cookies
        with requests.Session() as session:
            session.headers.update({
                "accept-language": "en-US,en;q=0.9",
                "sec-ch-ua": '"Chromium";v="130"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"Linux"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin"
            })
            
            status_message = "🔄 Starting merge process..."
            await interaction.followup.send(status_message, ephemeral=True)
            
            # Export data from each source URL
            for source_url in source_urls:
                status_message = f"🔄 Exporting data from {sanitize_url(source_url)}..."
                await interaction.followup.send(status_message, ephemeral=True)
                
                export_data = await export_plan(session, source_url)
                
                status_message = f"🔄 Importing data into {sanitize_url(target_url)}..."
                await interaction.followup.send(status_message, ephemeral=True)
                
                await import_plan(session, target_url, export_data)
        
        await interaction.followup.send("✅ Merge completed successfully!", ephemeral=True)

    except DSUltimateError as e:
        await interaction.followup.send(f"❌ Error during merge: {str(e)}", ephemeral=True)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await interaction.followup.send("❌ An unexpected error occurred", ephemeral=True)

@client.tree.command(name="merge", description="Merge multiple DS Ultimate attack plans")
async def merge_plans(interaction: discord.Interaction, target_url: str, source_urls: str):
    """
    Slash command to merge multiple DS Ultimate attack plans
    """
    # Acknowledge the interaction immediately
    await interaction.response.defer(ephemeral=True)
    
    # Split source URLs by whitespace or newline
    urls = [target_url] + source_urls.split()
    
    if len(urls) < 2:
        await interaction.followup.send("Please provide at least two URLs (one target and one source)", ephemeral=True)
        return

    # Validate all URLs
    invalid_urls = [url for url in urls if not validate_ds_ultimate_url(url)]
    if invalid_urls:
        sanitized_urls = [sanitize_url(url) for url in invalid_urls]
        await interaction.followup.send(f"Invalid URL(s) detected: {', '.join(sanitized_urls)}", ephemeral=True)
        return

    target_url = urls[0]
    source_urls = urls[1:]
    
    await do_merge(interaction, target_url, source_urls)

@client.tree.command(name="set-default", description="Set your default target URL for merging")
async def set_default_url(interaction: discord.Interaction, url: str = None):
    """Set a default target URL for merging"""
    if url is None:
        # Remove default URL
        if UserPreferences.remove_default_url(interaction.user.id):
            await interaction.response.send_message("✅ Your default target URL has been cleared.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ You didn't have a default target URL set.", ephemeral=True)
        return
    
    # Validate URL
    if not validate_ds_ultimate_url(url):
        await interaction.response.send_message("❌ Invalid URL format. Please provide a valid DS Ultimate attack planner URL.", ephemeral=True)
        return
    
    # Store the URL
    UserPreferences.set_default_url(interaction.user.id, url)
    await interaction.response.send_message("✅ Default target URL has been set.", ephemeral=True)

@client.tree.command(name="get-default", description="Show your current default target URL")
async def get_default_url(interaction: discord.Interaction):
    """Show your current default target URL"""
    url = UserPreferences.get_default_url(interaction.user.id)
    if url:
        await interaction.response.send_message(f"Your default target URL: {sanitize_url(url)}", ephemeral=True)
    else:
        await interaction.response.send_message("You haven't set a default target URL. Use /set-default to set one.", ephemeral=True)

@client.tree.command(name="merge-to-default", description="Merge plans into your default target")
async def merge_to_default(interaction: discord.Interaction, source_urls: str):
    """Merge plans into your default target"""
    # Acknowledge the interaction immediately
    await interaction.response.defer(ephemeral=True)
    
    # Get default URL
    target_url = UserPreferences.get_default_url(interaction.user.id)
    if not target_url:
        await interaction.followup.send("❌ No default target URL set. Use /set-default to set one.", ephemeral=True)
        return

    # Split source URLs by whitespace or newline
    source_url_list = source_urls.split()
    
    if not source_url_list:
        await interaction.followup.send("Please provide at least one source URL", ephemeral=True)
        return

    # Validate all URLs
    invalid_urls = [url for url in source_url_list if not validate_ds_ultimate_url(url)]
    if invalid_urls:
        sanitized_urls = [sanitize_url(url) for url in invalid_urls]
        await interaction.followup.send(f"Invalid URL(s) detected: {', '.join(sanitized_urls)}", ephemeral=True)
        return
    
    # Call the merge helper function
    await do_merge(interaction, target_url, source_url_list)

def main():
    """
    Main function to run the bot
    """
    client.run(TOKEN)

if __name__ == "__main__":
    main()
