#!/usr/bin/env python3
"""
Scrape Unitree G1 SDK Documentation
Uses Playwright for browser automation to handle dynamic content
"""

import asyncio
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright
import html2text

# Documentation URLs to scrape
URLS = [
    "https://support.unitree.com/home/en/G1_developer/about_G1",
    "https://support.unitree.com/home/en/G1_developer/Operational_guidance",
    "https://support.unitree.com/home/en/G1_developer/quick_start",
    "https://support.unitree.com/home/en/G1_developer/remote_control",
    "https://support.unitree.com/home/en/G1_developer/waist_fastener",
    "https://support.unitree.com/home/en/G1_developer/voice_assistant_instructions",
    "https://support.unitree.com/home/en/G1_developer/audio_playback",
    "https://support.unitree.com/home/en/G1_developer/application_development",
    "https://support.unitree.com/home/en/G1_developer/sdk_overview",
    "https://support.unitree.com/home/en/G1_developer/architecture_description",
    "https://support.unitree.com/home/en/G1_developer/get_sdk",
    "https://support.unitree.com/home/en/G1_developer/quick_development",
    "https://support.unitree.com/home/en/G1_developer/basic_motion_development",
    "https://support.unitree.com/home/en/G1_developer/basic_motion_routine",
    "https://support.unitree.com/home/en/G1_developer/joint_motor_sequence",
    "https://support.unitree.com/home/en/G1_developer/remote_control_data",
    "https://support.unitree.com/home/en/G1_developer/dexterous_hand",
    "https://support.unitree.com/home/en/G1_developer/inspire_ftp_dexterity_hand",
    "https://support.unitree.com/home/en/G1_developer/inspire_dfx_dexterous_hand",
    "https://support.unitree.com/home/en/G1_developer/brainco_hand",
    "https://support.unitree.com/home/en/G1_developer/services_interface",
    "https://support.unitree.com/home/en/G1_developer/dds_services_interface",
    "https://support.unitree.com/home/en/G1_developer/robot_state_client_interface",
    "https://support.unitree.com/home/en/G1_developer/basic_services_interface",
    "https://support.unitree.com/home/en/G1_developer/sport_services_interface",
    "https://support.unitree.com/home/en/G1_developer/odometer_service_interface",
    "https://support.unitree.com/home/en/G1_developer/VuiClient_Service",
    "https://support.unitree.com/home/en/G1_developer/lidar_services_interface",
    "https://support.unitree.com/home/en/G1_developer/slam_navigation_services_interface",
    "https://support.unitree.com/home/en/G1_developer/motion_witcher_service_interface",
    "https://support.unitree.com/home/en/G1_developer/high_motion_development",
    "https://support.unitree.com/home/en/G1_developer/rpc_routine",
    "https://support.unitree.com/home/en/G1_developer/arm_control_routine",
    "https://support.unitree.com/home/en/G1_developer/arm_action_interface",
    "https://support.unitree.com/home/en/G1_developer/more_cases",
    "https://support.unitree.com/home/en/G1_developer/rl_control_routine",
    "https://support.unitree.com/home/en/G1_developer/ros2_communication_routine",
    "https://support.unitree.com/home/en/G1_developer/dds_communication_routine",
    "https://support.unitree.com/home/en/G1_developer/lidar_Instructions",
    "https://support.unitree.com/home/en/G1_developer/depth_camera_instruction",
    "https://support.unitree.com/home/en/G1_developer/debugging_specification",
    "https://support.unitree.com/home/en/G1_developer/FAQ",
    "https://support.unitree.com/home/en/G1_developer/common_istakes_and_definitions",
]

OUTPUT_DIR = Path("unitree_docs")
IMAGES_DIR = OUTPUT_DIR / "images"


def sanitize_filename(url: str) -> str:
    """Convert URL to safe filename"""
    # Extract the last part of URL path
    name = url.split("/")[-1]
    # Replace underscores with hyphens for readability
    name = name.replace("_", "-")
    return f"{name}.md"


async def download_image(page, img_url: str, output_path: Path) -> str:
    """Download an image and return local path"""
    try:
        # Make URL absolute if relative
        if img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url.startswith("/"):
            img_url = "https://support.unitree.com" + img_url
        
        # Download image
        response = await page.context.request.get(img_url)
        if response.ok:
            img_data = await response.body()
            
            # Create filename from URL
            img_filename = img_url.split("/")[-1].split("?")[0]
            if not img_filename:
                img_filename = f"image_{hash(img_url)}.png"
            
            img_path = IMAGES_DIR / img_filename
            img_path.write_bytes(img_data)
            
            # Return relative path for markdown
            return f"images/{img_filename}"
        
    except Exception as e:
        print(f"  ⚠️  Failed to download image {img_url}: {e}")
    
    return img_url  # Return original URL if download fails


async def scrape_page(page, url: str, output_dir: Path) -> bool:
    """Scrape a single documentation page"""
    filename = sanitize_filename(url)
    output_path = output_dir / filename
    
    print(f"\n📄 Scraping: {url}")
    print(f"   → {filename}")
    
    try:
        # Navigate to page
        await page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Wait for main content to load (adjust selector based on actual page structure)
        await page.wait_for_selector("article, .content, .markdown-body, main", timeout=10000)
        
        # Additional wait for dynamic content
        await asyncio.sleep(2)
        
        # Try multiple selectors to find main content
        content_html = None
        selectors = [
            "article",
            ".markdown-body",
            ".content-body",
            ".doc-content",
            "main",
            "#content",
            ".page-content",
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    content_html = await element.inner_html()
                    if content_html and len(content_html) > 100:  # Ensure we got meaningful content
                        print(f"   ✓ Found content using selector: {selector}")
                        break
            except:
                continue
        
        if not content_html:
            # Fallback: get entire body
            content_html = await page.content()
            print(f"   ⚠️  Using full page content (no specific selector matched)")
        
        # Download images
        img_elements = await page.query_selector_all("img")
        img_map = {}
        
        for img in img_elements:
            src = await img.get_attribute("src")
            if src and not src.startswith("data:"):
                local_path = await download_image(page, src, output_dir)
                img_map[src] = local_path
        
        # Replace image URLs in HTML
        for original, local in img_map.items():
            content_html = content_html.replace(original, local)
        
        # Convert HTML to Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        h.ignore_emphasis = False
        h.body_width = 0  # Don't wrap lines
        h.single_line_break = False
        
        markdown = h.handle(content_html)
        
        # Add metadata header
        header = f"""# {url.split('/')[-1].replace('_', ' ').title()}

**Source:** {url}  
**Scraped:** {asyncio.get_event_loop().time()}

---

"""
        
        markdown = header + markdown
        
        # Save to file
        output_path.write_text(markdown, encoding="utf-8")
        
        print(f"   ✅ Saved to {output_path}")
        print(f"   📊 Size: {len(markdown)} chars, {len(img_map)} images")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


async def main():
    """Main scraping function"""
    # Create output directories
    OUTPUT_DIR.mkdir(exist_ok=True)
    IMAGES_DIR.mkdir(exist_ok=True)
    
    print("=" * 70)
    print("Unitree G1 SDK Documentation Scraper")
    print("=" * 70)
    print(f"📁 Output directory: {OUTPUT_DIR.absolute()}")
    print(f"🖼️  Images directory: {IMAGES_DIR.absolute()}")
    print(f"📚 Total pages to scrape: {len(URLS)}")
    
    async with async_playwright() as p:
        # Launch browser (headless=False to see what's happening)
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
        )
        page = await context.new_page()
        
        # Scrape each URL
        success_count = 0
        failed_urls = []
        
        for i, url in enumerate(URLS, 1):
            print(f"\n[{i}/{len(URLS)}]", end=" ")
            
            success = await scrape_page(page, url, OUTPUT_DIR)
            
            if success:
                success_count += 1
            else:
                failed_urls.append(url)
            
            # Be nice to the server
            await asyncio.sleep(1)
        
        await browser.close()
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 Scraping Complete!")
    print("=" * 70)
    print(f"✅ Successful: {success_count}/{len(URLS)}")
    print(f"❌ Failed: {len(failed_urls)}/{len(URLS)}")
    
    if failed_urls:
        print("\n⚠️  Failed URLs:")
        for url in failed_urls:
            print(f"   - {url}")
    
    print(f"\n📁 Documentation saved to: {OUTPUT_DIR.absolute()}")
    print(f"🖼️  Images saved to: {IMAGES_DIR.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
