import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(page_title="Website Crawler", layout="wide")
st.title("🕷️ Website Crawler")

max_pages = st.sidebar.slider("Max pages", 10, 200, 50)
timeout = st.sidebar.slider("Timeout (sec)", 5, 60, 30)

def get_domain(url):
    try:
        return urlparse(url).netloc.lower()
    except:
        return None

def get_subdomains(urls, base_domain):
    subdomains = set()
    for url in urls:
        domain = get_domain(url)
        if domain and domain.endswith(base_domain) and domain != base_domain:
            subdomains.add(domain)
    return sorted(list(subdomains))

def fetch_links(url, timeout):
    try:
        resp = requests.get(url, timeout=timeout, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(resp.content, 'html.parser')
        links = [urljoin(url, a.get('href')) for a in soup.find_all('a', href=True)]
        return [l for l in links if l and not l.startswith('#')], None
    except Exception as e:
        return [], str(e)[:50]

def crawl(start_url, max_pages, timeout, workers=3):
    if not start_url.startswith(('http://', 'https://')):
        start_url = 'https://' + start_url
    
    base_domain = get_domain(start_url)
    visited = set()
    all_urls = set()
    errors = []
    queue = [start_url]
    
    status = st.empty()
    progress = st.progress(0)
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {}
        
        while queue and len(visited) < max_pages:
            while queue and len(futures) < workers and len(visited) < max_pages:
                url = queue.pop(0)
                if url not in visited:
                    visited.add(url)
                    futures[executor.submit(fetch_links, url, timeout)] = url
            
            for future in as_completed(futures):
                url = futures.pop(future)
                status.info(f"🔍 Crawled: {len(visited)}/{max_pages} - {url[:50]}")
                progress.progress(len(visited) / max_pages)
                
                try:
                    links, err = future.result()
                    if err:
                        errors.append(err)
                    
                    for link in links:
                        domain = get_domain(link)
                        if domain and (domain == base_domain or domain.endswith('.' + base_domain)):
                            all_urls.add(link)
                            if link not in visited and len(visited) < max_pages:
                                queue.append(link)
                except:
                    pass
    
    return visited, all_urls, get_subdomains(all_urls, base_domain), errors

col1, col2 = st.columns([3, 1])
with col1:
    url_input = st.text_input("Website URL", placeholder="example.com")
with col2:
    if st.button("🚀 Crawl", use_container_width=True, type="primary"):
        if url_input:
            st.divider()
            visited, all_urls, subdomains, errors = crawl(url_input, max_pages, timeout)
            
            st.success("✅ Done!")
            col1, col2, col3 = st.columns(3)
            col1.metric("Pages", len(visited))
            col2.metric("URLs", len(all_urls))
            col3.metric("Subdomains", len(subdomains))
            
            st.divider()
            if subdomains:
                st.subheader("Subdomains")
                for sd in subdomains:
                    st.write(f"• `{sd}`")
                st.download_button("📥 Download", "\n".join(subdomains), "subdomains.txt", "text/plain")
            
            st.divider()
            st.subheader("All URLs")
            st.text_area("URLs:", "\n".join(sorted(all_urls)), height=200, disabled=True)
            st.download_button("📥 Download", "\n".join(sorted(all_urls)), "urls.txt", "text/plain")
