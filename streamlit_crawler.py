import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Website Crawler", layout="wide")
st.title("🕷️ Website Crawler - Subdomain & URL Finder")

st.sidebar.write("### Settings")
max_pages = st.sidebar.slider("Max pages to crawl", 10, 500, 50)
timeout_sec = st.sidebar.slider("Timeout (seconds)", 5, 60, 30)
include_external = st.sidebar.checkbox("Include external links", False)
max_workers = st.sidebar.slider("Concurrent requests", 1, 10, 3)


def extract_domain(url):
    """Extract base domain from URL."""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return None


def extract_subdomains(urls, base_domain):
    """Extract all unique subdomains from a list of URLs."""
    subdomains = set()
    base_domain_lower = base_domain.lower()
    
    for url in urls:
        try:
            domain = extract_domain(url)
            if domain and domain.endswith(base_domain_lower) and domain != base_domain_lower:
                subdomains.add(domain)
        except:
            pass
    
    return sorted(list(subdomains))


def is_valid_url(url, base_domain):
    """Check if URL belongs to the same domain or subdomain."""
    try:
        domain = extract_domain(url)
        if not domain:
            return False
        base_lower = base_domain.lower()
        return domain == base_lower or domain.endswith("." + base_lower)
    except:
        return False


def fetch_page(url, timeout_sec):
    """Fetch a single page and extract links."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, timeout=timeout_sec, headers=headers, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()
            if href and not href.startswith('#'):
                absolute_url = urljoin(url, href)
                links.append(absolute_url)
        
        return links, None
    except requests.exceptions.Timeout:
        return [], f"Timeout: {url[:60]}"
    except requests.exceptions.ConnectionError:
        return [], f"Connection error: {url[:60]}"
    except Exception as e:
        return [], f"Error on {url[:60]}: {str(e)[:50]}"


def crawl_website(start_url, max_pages, timeout_sec, include_external, max_workers):
    """Crawl website and collect all URLs and subdomains."""
    visited_urls = set()
    all_urls = set()
    subdomains = set()
    errors = []
    
    base_domain = extract_domain(start_url)
    if not base_domain:
        return {
            "visited_urls": [],
            "all_urls": [],
            "subdomains": [],
            "base_domain": "invalid",
            "errors": ["Invalid URL"]
        }
    
    status_placeholder = st.empty()
    progress_bar = st.progress(0)
    
    # Normalize start URL
    if not start_url.startswith(("http://", "https://")):
        start_url = "https://" + start_url
    
    queue = [start_url]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        
        while queue and len(visited_urls) < max_pages:
            # Submit new tasks
            while queue and len(futures) < max_workers and len(visited_urls) < max_pages:
                current_url = queue.pop(0)
                
                if current_url in visited_urls:
                    continue
                
                visited_urls.add(current_url)
                future = executor.submit(fetch_page, current_url, timeout_sec)
                futures[future] = current_url
            
            # Process completed tasks
            for future in as_completed(futures):
                url = futures.pop(future)
                
                progress = len(visited_urls) / max_pages
                progress_bar.progress(min(progress, 1.0))
                status_placeholder.info(f"🔍 Crawling ({len(visited_urls)}/{max_pages}): {url[:60]}...")
                
                try:
                    links, error = future.result()
                    
                    if error:
                        errors.append(error)
                    
                    for link in links:
                        try:
                            parsed = urlparse(link)
                            
                            if not parsed.scheme:
                                continue
                            
                            link_domain = extract_domain(link)
                            
                            if include_external or is_valid_url(link, base_domain):
                                all_urls.add(link)
                                
                                if is_valid_url(link, base_domain):
                                    # Track subdomains
                                    if link_domain and link_domain.endswith("." + base_domain.lower()):
                                        subdomains.add(link_domain)
                                    
                                    if link not in visited_urls and len(visited_urls) < max_pages:
                                        queue.append(link)
                        except Exception as e:
                            continue
                
                except Exception as e:
                    errors.append(f"Error processing {url}: {str(e)[:50]}")
    
    return {
        "visited_urls": sorted(list(visited_urls)),
        "all_urls": sorted(list(all_urls)),
        "subdomains": sorted(list(subdomains)) if subdomains else sorted(list(extract_subdomains(all_urls, base_domain))),
        "base_domain": base_domain,
        "errors": errors
    }


# Main UI
col1, col2 = st.columns([3, 1])

with col1:
    website_url = st.text_input(
        "Enter website URL",
        placeholder="example.com or https://example.com",
        help="Enter the website you want to crawl"
    )

with col2:
    start_button = st.button("🚀 Start Crawling", use_container_width=True, type="primary")

if start_button and website_url:
    try:
        # Validate URL
        if not website_url.startswith(("http://", "https://")):
            test_url = "https://" + website_url
        else:
            test_url = website_url
        
        urlparse(test_url)
        
        st.divider()
        
        with st.spinner("🔄 Crawling website... This may take a moment."):
            results = crawl_website(
                test_url,
                max_pages,
                timeout_sec,
                include_external,
                max_workers
            )
        
        # Display Results
        st.success("✅ Crawling completed!")
        
        # Summary cards
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Base Domain", results["base_domain"])
        with col2:
            st.metric("Pages Crawled", len(results["visited_urls"]))
        with col3:
            st.metric("Total URLs Found", len(results["all_urls"]))
        with col4:
            st.metric("Subdomains Found", len(results["subdomains"]))
        
        st.divider()
        
        # Display subdomains
        if results["subdomains"]:
            st.subheader("🌐 Discovered Subdomains")
            with st.expander(f"View {len(results['subdomains'])} subdomains", expanded=True):
                for i, subdomain in enumerate(results["subdomains"], 1):
                    st.write(f"{i}. `{subdomain}`")
                
                # Download subdomains
                subdomains_text = "\n".join(results["subdomains"])
                st.download_button(
                    label="📥 Download Subdomains (TXT)",
                    data=subdomains_text,
                    file_name=f"{results['base_domain']}_subdomains.txt",
                    mime="text/plain"
                )
        else:
            st.info("No subdomains found (website may only use main domain)")
        
        st.divider()
        
        # Display all URLs
        st.subheader("🔗 All URLs Found")
        with st.expander(f"View {len(results['all_urls'])} URLs", expanded=False):
            urls_text = "\n".join(results["all_urls"])
            st.text_area(
                "All discovered URLs:",
                urls_text,
                height=300,
                disabled=True
            )
            
            # Download URLs
            st.download_button(
                label="📥 Download All URLs (TXT)",
                data=urls_text,
                file_name=f"{results['base_domain']}_urls.txt",
                mime="text/plain"
            )
        
        # Display errors
        if results["errors"]:
            st.divider()
            with st.expander("⚠️ Errors & Warnings", expanded=False):
                for error in results["errors"][:10]:  # Show first 10 errors
                    st.warning(error)
    
    except Exception as e:
        st.error(f"❌ Invalid URL or error: {str(e)}")

st.divider()
st.caption("💡 Tips: Use low max pages for faster results. Increase timeout for slow websites.")
