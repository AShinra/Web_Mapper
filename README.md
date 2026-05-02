# Website Crawler with Subdomain Finder

A Streamlit-based web crawler that discovers all URLs and subdomains from a target website using Playwright.

## Features

✨ **Core Capabilities:**
- Enter any website URL and crawl it automatically
- Extract all discovered URLs and subdomains
- Configurable crawling depth (max pages)
- Adjustable timeout settings
- Option to include external links
- Download results as TXT files
- Real-time progress tracking
- Error handling and reporting

## Installation

### Local Development

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. Run locally:
```bash
streamlit run streamlit_crawler.py
```

## Deployment to Streamlit Cloud

### Step 1: Prepare your GitHub repository
1. Create a new GitHub repository
2. Push these files:
   - `streamlit_crawler.py` (main app)
   - `requirements.txt` (dependencies)
   - `.streamlit/config.toml` (Streamlit configuration)
   - `README.md` (this file)

### Step 2: Deploy to Streamlit Cloud
1. Go to [Streamlit Cloud](https://share.streamlit.io/)
2. Sign in with your GitHub account
3. Click "New app"
4. Select your repository
5. Specify the file: `streamlit_crawler.py`
6. Click "Deploy"

### Step 3: Handle Playwright on Cloud (IMPORTANT!)

Streamlit Cloud requires special handling for Playwright. Add a `packages.txt` file:

**packages.txt** (create this file):
```
libgconf-2-4
libx11-xcb1
libxcomposite1
libxcursor1
libxdamage1
libxext6
libxfixes3
libxi6
libxinerama1
libxrandr2
libxrender1
libxss1
libxtst6
fonts-liberation
libappindicator1
libgtk-3-0
xdg-utils
```

## Usage

1. **Enter Website URL**: Input your target website (e.g., `example.com` or `https://example.com`)
2. **Configure Settings** (sidebar):
   - Max Pages: How many pages to crawl (default: 50)
   - Timeout: Max seconds per page (default: 30)
   - Include External Links: Toggle for external URLs
3. **Click "Start Crawling"**: The app will begin crawling
4. **View Results**:
   - Summary cards showing statistics
   - Discovered subdomains list
   - All URLs found
   - Download options for results

## Configuration Options

### Sidebar Settings

- **Max pages to crawl** (10-500): Limits the number of pages to visit. Lower values = faster, less comprehensive.
- **Timeout (seconds)** (5-60): How long to wait for each page to load.
- **Include external links**: Whether to collect links pointing outside the target domain.

## File Structure

```
Web_Mapper/
├── streamlit_crawler.py      # Main application
├── requirements.txt          # Python dependencies
├── packages.txt             # System packages (for Streamlit Cloud)
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── README.md                # This file
```

## How It Works

1. **URL Normalization**: Converts input URL to proper format
2. **Domain Extraction**: Identifies the base domain
3. **Web Crawling**: Uses Playwright to:
   - Load each page
   - Extract all links via DOM query
   - Resolve relative URLs to absolute URLs
   - Filter by domain (stays on-domain by default)
4. **Subdomain Detection**: Identifies URLs with subdomains
5. **Results Display**: Shows statistics and allows downloading results

## Technical Details

- **Framework**: Streamlit 1.36.0
- **Browser Automation**: Playwright 1.44.0 (Chromium)
- **Execution**: Asynchronous with asyncio
- **URL Parsing**: Python's urllib.parse

## Performance Tips

- Start with lower max pages (20-30) for quick tests
- Increase timeout for slow websites
- On Streamlit Cloud, initial load may take 30-60 seconds

## Troubleshooting

**"Browser error"**: Website may be blocking automated browsers
- Try increasing timeout
- Check if website has anti-bot protection

**"Timeout errors"**: Website is slow to load
- Increase timeout setting
- Reduce max pages to crawl

**"No results"**: Website may be JavaScript-heavy
- The crawler waits for `domcontentloaded` event

## Limitations

- Does not execute complex JavaScript (waits for DOM ready only)
- Does not handle sites requiring authentication
- Respects only crawl speed, not robots.txt (use responsibly!)
- Some websites may block automated access

## License

MIT License - Feel free to modify and deploy!

## Support

For issues or questions, check the error messages in the app or review the logs in Streamlit Cloud deployment dashboard.
