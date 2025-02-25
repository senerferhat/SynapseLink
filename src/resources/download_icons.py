import os
import urllib.request
from pathlib import Path

ICON_URLS = {
    'new_connection.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/plug.svg',
    'save.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/save.svg',
    'load.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/folder-open.svg',
    'split_view.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/columns.svg',
    'protocol.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/network-wired.svg',
    'automation.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/robot.svg',
    'dark_mode.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/moon.svg',
    'security.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/shield-alt.svg',
    'user.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/users-cog.svg',
    'export.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/file-export.svg',
    'search.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/search.svg',
    'settings.png': 'https://raw.githubusercontent.com/FortAwesome/Font-Awesome/master/svgs/solid/cog.svg'
}

def download_icons():
    """Download and prepare icons for the application."""
    current_dir = Path(__file__).parent
    icons_dir = current_dir / 'icons'
    icons_dir.mkdir(exist_ok=True)
    
    for icon_name, url in ICON_URLS.items():
        icon_path = icons_dir / icon_name
        if not icon_path.exists():
            try:
                print(f"Downloading {icon_name}...")
                urllib.request.urlretrieve(url, icon_path)
                print(f"Successfully downloaded {icon_name}")
            except Exception as e:
                print(f"Failed to download {icon_name}: {str(e)}")
                continue

    print("\nAll icons have been downloaded.")
    print("Note: SVG files need to be converted to PNG format.")
    print("Please use an SVG to PNG converter or image editing software to convert the icons.")

if __name__ == '__main__':
    download_icons() 