import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import re

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

def generate_regex(urls):
    """Generate regex pattern from selected URLs"""
    if not urls:
        return ""
    
    patterns = []
    for url in urls:
        parsed = urlparse(url)
        path = parsed.path
        if path:
            patterns.append(re.escape(path))
    
    if patterns:
        combined = "|".join(patterns)
        return f"({combined})"
    return ""

# Initialize session state
if 'crawler_run' not in st.session_state:
    st.session_state.crawler_run = False
if 'section_regexes' not in st.session_state:
    st.session_state.section_regexes = []
if 'article_regexes' not in st.session_state:
    st.session_state.article_regexes = []
if 'ignore_regexes' not in st.session_state:
    st.session_state.ignore_regexes = []

# Input section
col1, col2 = st.columns([3, 1])
with col1:
    url_input = st.text_input("Website URL", placeholder="example.com", key="url_input")
with col2:
    if st.button("🚀 Crawl", use_container_width=True, type="primary"):
        if url_input:
            st.session_state.visited, st.session_state.all_urls, st.session_state.subdomains, st.session_state.errors = crawl(url_input, max_pages, timeout)
            st.session_state.crawler_run = True

if st.session_state.crawler_run:
    st.divider()
    
    # Summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Pages", len(st.session_state.visited))
    col2.metric("URLs", len(st.session_state.all_urls))
    col3.metric("Subdomains", len(st.session_state.subdomains))
    
    st.divider()
    
    # Subdomains with toggles
    if st.session_state.subdomains:
        st.subheader("🌐 Subdomains")
        
        for sd in st.session_state.subdomains:
            if sd not in st.session_state:
                st.session_state[sd] = True
        
        for sd in st.session_state.subdomains:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"• `{sd}`")
            with col2:
                st.session_state[sd] = st.toggle("Active", value=st.session_state[sd], key=f"toggle_{sd}")
        
        st.divider()
        
        # Save subdomains button
        if st.button("💾 Save Active Subdomains", use_container_width=True):
            active = [sd for sd in st.session_state.subdomains if st.session_state.get(sd, True)]
            if active:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"subdomains_{timestamp}.txt"
                content = "\n".join(active)
                st.success(f"✅ {len(active)} subdomains ready!")
                st.download_button("📥 Download", content, filename, "text/plain", use_container_width=True)
    
    st.divider()
    
    # URL Categorization
    st.subheader("📂 Categorize URLs")
    
    urls_list = sorted(list(st.session_state.all_urls))
    
    col1, col2, col3 = st.columns(3)
    
    # Section Card
    with col1:
        st.markdown("### 📄 Section")
        section_urls = st.multiselect(
            "Select URLs for Section",
            urls_list,
            key="section_urls",
            label_visibility="collapsed"
        )
        
        if section_urls:
            if st.button("🔧 Generate Regex", key="section_regex_btn", use_container_width=True):
                regex = generate_regex(section_urls)
                if regex:
                    st.session_state.section_regexes.append(regex)
        
        # Manual regex input
        manual_section = st.text_input("Add custom regex", key="manual_section", placeholder="e.g., (pattern1|pattern2)")
        if manual_section and st.button("➕ Add", key="add_section", use_container_width=True):
            st.session_state.section_regexes.append(manual_section)
            st.success("✅ Regex added!")
        
        # Display regexes
        if st.session_state.section_regexes:
            st.markdown("**Regex Results:**")
            for i, regex in enumerate(st.session_state.section_regexes):
                col_reg, col_del = st.columns([4, 1])
                with col_reg:
                    st.code(regex, language="regex")
                with col_del:
                    if st.button("🗑️", key=f"del_section_{i}", use_container_width=True):
                        st.session_state.section_regexes.pop(i)
                        st.rerun()
    
    # Article Card
    with col2:
        st.markdown("### 📰 Article")
        article_urls = st.multiselect(
            "Select URLs for Article",
            urls_list,
            key="article_urls",
            label_visibility="collapsed"
        )
        
        if article_urls:
            if st.button("🔧 Generate Regex", key="article_regex_btn", use_container_width=True):
                regex = generate_regex(article_urls)
                if regex:
                    st.session_state.article_regexes.append(regex)
        
        # Manual regex input
        manual_article = st.text_input("Add custom regex", key="manual_article", placeholder="e.g., (pattern1|pattern2)")
        if manual_article and st.button("➕ Add", key="add_article", use_container_width=True):
            st.session_state.article_regexes.append(manual_article)
            st.success("✅ Regex added!")
        
        # Display regexes
        if st.session_state.article_regexes:
            st.markdown("**Regex Results:**")
            for i, regex in enumerate(st.session_state.article_regexes):
                col_reg, col_del = st.columns([4, 1])
                with col_reg:
                    st.code(regex, language="regex")
                with col_del:
                    if st.button("🗑️", key=f"del_article_{i}", use_container_width=True):
                        st.session_state.article_regexes.pop(i)
                        st.rerun()
    
    # Ignore Card
    with col3:
        st.markdown("### 🚫 Ignore")
        ignore_urls = st.multiselect(
            "Select URLs for Ignore",
            urls_list,
            key="ignore_urls",
            label_visibility="collapsed"
        )
        
        if ignore_urls:
            if st.button("🔧 Generate Regex", key="ignore_regex_btn", use_container_width=True):
                regex = generate_regex(ignore_urls)
                if regex:
                    st.session_state.ignore_regexes.append(regex)
        
        # Manual regex input
        manual_ignore = st.text_input("Add custom regex", key="manual_ignore", placeholder="e.g., (pattern1|pattern2)")
        if manual_ignore and st.button("➕ Add", key="add_ignore", use_container_width=True):
            st.session_state.ignore_regexes.append(manual_ignore)
            st.success("✅ Regex added!")
        
        # Display regexes
        if st.session_state.ignore_regexes:
            st.markdown("**Regex Results:**")
            for i, regex in enumerate(st.session_state.ignore_regexes):
                col_reg, col_del = st.columns([4, 1])
                with col_reg:
                    st.code(regex, language="regex")
                with col_del:
                    if st.button("🗑️", key=f"del_ignore_{i}", use_container_width=True):
                        st.session_state.ignore_regexes.pop(i)
                        st.rerun()
    
    st.divider()
    
    # Download all regexes
    if st.session_state.section_regexes or st.session_state.article_regexes or st.session_state.ignore_regexes:
        st.subheader("💾 Save Configuration")
        
        config_content = ""
        if st.session_state.section_regexes:
            config_content += "# SECTION\n" + "\n".join(st.session_state.section_regexes) + "\n\n"
        if st.session_state.article_regexes:
            config_content += "# ARTICLE\n" + "\n".join(st.session_state.article_regexes) + "\n\n"
        if st.session_state.ignore_regexes:
            config_content += "# IGNORE\n" + "\n".join(st.session_state.ignore_regexes) + "\n\n"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.download_button(
            "📥 Download Config",
            config_content,
            f"regex_config_{timestamp}.txt",
            "text/plain",
            use_container_width=True
        )
    
    st.divider()
    
    # All URLs
    st.subheader("🔗 All URLs")
    with st.expander(f"View {len(st.session_state.all_urls)} URLs"):
        urls_content = "\n".join(sorted(st.session_state.all_urls))
        st.text_area("URLs:", urls_content, height=200, disabled=True)
        st.download_button("📥 Download URLs", urls_content, "urls.txt", "text/plain", use_container_width=True)
