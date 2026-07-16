from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import html
import re

router = APIRouter(prefix="/api/news", tags=["News"])

class NewsArticle(BaseModel):
    id: str
    category: str
    title: str
    desc: str
    image: str
    url: str

def parse_big_company_rss(category: str) -> List[NewsArticle]:
    feeds = {
        "Finance": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
        "Technology": "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
        "Startups": "https://rss.nytimes.com/services/xml/rss/nyt/SmallBusiness.xml",
        "Economy": "https://rss.nytimes.com/services/xml/rss/nyt/Economy.xml",
        "Markets": "http://feeds.bbci.co.uk/news/business/rss.xml"
    }
    
    url = feeds.get(category, "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml")
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"Error fetching RSS: {e}")
        return []

    try:
        root = ET.fromstring(xml_data)
        channel = root.find("channel")
        items = channel.findall("item") if channel is not None else []
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return []
    
    articles = []
    
    # Fallback images in case an article misses the image tag
    default_images = {
        "Finance": "https://images.unsplash.com/photo-1611974789855-9c2a0a7236a3?auto=format&fit=crop&w=600&q=80",
        "Technology": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=600&q=80",
        "Startups": "https://images.unsplash.com/photo-1556761175-4b46a572b786?auto=format&fit=crop&w=600&q=80",
        "Markets": "https://images.unsplash.com/photo-1516199423456-1f1e91b06f25?auto=format&fit=crop&w=600&q=80",
        "Economy": "https://images.unsplash.com/photo-1441986300917-64674bd600d8?auto=format&fit=crop&w=600&q=80"
    }
    fallback_image = default_images.get(category, "https://images.unsplash.com/photo-1526304640581-d334cdbbf45e?auto=format&fit=crop&w=600&q=80")

    for idx, item in enumerate(items[:12]): # Top 12
        title_el = item.find("title")
        link_el = item.find("link")
        desc_el = item.find("description")
        
        raw_title = title_el.text if title_el is not None and title_el.text is not None else ""
        raw_link = link_el.text if link_el is not None and link_el.text is not None else "#"
        raw_desc = desc_el.text if desc_el is not None and desc_el.text is not None else ""
        
        # Find image using mrss namespace or similar
        image = fallback_image
        
        # New York Times uses <media:content> or <ns2:content> 
        # BBC uses <media:thumbnail> or <ns0:thumbnail>
        # Let's search all tags for an image URL
        for child in item:
            tag_name = child.tag.lower()
            if 'content' in tag_name or 'thumbnail' in tag_name:
                url_attr = child.get('url')
                if url_attr:
                    image = url_attr
                    break
                
        desc_text = raw_desc
        
        # Strip HTML from desc just in case
        if '<' in raw_desc:
            desc_text = re.sub(r'<[^>]+>', '', raw_desc)
            if not desc_text.strip():
                desc_text = raw_title
                
        desc_text = html.unescape(desc_text).strip()
        title = html.unescape(raw_title).strip()
            
        articles.append(NewsArticle(
            id=str(idx) + raw_link[-10:],
            category=category,
            title=title,
            desc=desc_text[:150] + "..." if len(desc_text) > 150 else desc_text,
            image=image,
            url=raw_link
        ))

    return articles

@router.get("/", response_model=List[NewsArticle])
def get_news(category: str = "Finance"):
    articles = parse_big_company_rss(category)
    return articles
