import requests
from bs4 import BeautifulSoup
import chardet
from urllib.parse import urljoin

class RussianTextFetcher:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url):
        """Fetch page with proper encoding detection"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Method 1: Use chardet to detect encoding
            detected = chardet.detect(response.content)
            detected_encoding = detected['encoding']
            confidence = detected['confidence']
            
            print(f"Detected encoding: {detected_encoding} (confidence: {confidence:.2f})")
            
            # Method 2: Try apparent encoding from requests
            apparent_encoding = response.apparent_encoding
            print(f"Apparent encoding: {apparent_encoding}")
            
            # Method 3: Check server-declared encoding
            server_encoding = response.encoding
            print(f"Server declared encoding: {server_encoding}")
            
            # Try encodings in order of preference
            encodings_to_try = [
                detected_encoding,
                apparent_encoding, 
                server_encoding,
                'utf-8',
                'windows-1251',
                'koi8-r',
                'iso-8859-5'
            ]
            
            # Remove None values and duplicates while preserving order
            seen = set()
            encodings_to_try = [x for x in encodings_to_try 
                              if x is not None and not (x in seen or seen.add(x))]
            
            for encoding in encodings_to_try:
                try:
                    text = response.content.decode(encoding)
                    print(f"✓ Successfully decoded with: {encoding}")
                    return text, encoding
                except (UnicodeDecodeError, UnicodeError, LookupError) as e:
                    print(f"✗ Failed with {encoding}: {e}")
                    continue
            
            raise ValueError("Could not decode content with any encoding")
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch URL: {e}")
    
    def extract_text(self, html_content):
        """Extract clean text from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it up
        text = soup.get_text()
        
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text, soup
    
    def fetch_and_extract(self, url):
        """Main method to fetch and extract text"""
        print(f"Fetching: {url}")
        html_content, encoding = self.fetch_page(url)
        text, soup = self.extract_text(html_content)
        
        return {
            'url': url,
            'text': text,
            'soup': soup,
            'encoding': encoding,
            'title': soup.title.string if soup.title else 'No title'
        }

# Example usage
if __name__ == "__main__":
    fetcher = RussianTextFetcher()
    
    # Replace with actual theravada.ru URL
    url = "https://тхеравада.рф/palicanon/суттанта/мадджхима-hикая"  # Replace with specific page
    
    try:
        result = fetcher.fetch_and_extract(url)
        
        print(f"\nTitle: {result['title']}")
        print(f"Encoding used: {result['encoding']}")
        print(f"Text length: {len(result['text'])} characters")
        print("\nFirst 500 characters:")
        print(result['text'][:500])
        print("...")
        
    except Exception as e:
        print(f"Error: {e}")