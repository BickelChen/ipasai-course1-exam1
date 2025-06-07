import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def download_file(url, folder):
    filename = os.path.basename(urlparse(url).path)
    if not filename:
        filename = 'index'
    local_path = os.path.join(folder, filename)
    r = requests.get(url, stream=True)
    r.raise_for_status()
    with open(local_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return local_path


def main():
    url = input("Enter URL: ").strip()
    if not url:
        print("No URL provided")
        return
    if not urlparse(url).scheme:
        url = 'http://' + url

    response = requests.get(url)
    response.raise_for_status()
    html = response.text

    save_dir = 'downloaded_files'
    os.makedirs(save_dir, exist_ok=True)

    html_file = os.path.join(save_dir, 'page.html')
    with open(html_file, 'w', encoding=response.encoding or 'utf-8') as f:
        f.write(html)
    print(f"Saved main page to {html_file}")

    choice = input("Download linked resources? (y/n): ").strip().lower()
    if choice != 'y':
        return

    soup = BeautifulSoup(html, 'html.parser')
    resource_urls = []
    for tag in soup.find_all(['img', 'script', 'link', 'a']):
        if tag.name == 'img' and tag.get('src'):
            resource_urls.append(urljoin(url, tag['src']))
        elif tag.name == 'script' and tag.get('src'):
            resource_urls.append(urljoin(url, tag['src']))
        elif tag.name == 'link' and tag.get('href'):
            if tag.get('rel') and 'stylesheet' in tag.get('rel'):
                resource_urls.append(urljoin(url, tag['href']))
        elif tag.name == 'a' and tag.get('href'):
            href = tag['href']
            if not href.startswith('#'):
                resource_urls.append(urljoin(url, href))

    seen = set()
    for res_url in resource_urls:
        if res_url in seen:
            continue
        seen.add(res_url)
        try:
            print(f"Downloading {res_url}...")
            download_file(res_url, save_dir)
        except Exception as e:
            print(f"Failed to download {res_url}: {e}")


if __name__ == '__main__':
    main()
