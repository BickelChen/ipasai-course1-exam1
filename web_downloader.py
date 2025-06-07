from flask import Flask, render_template, request, send_file
import os
import shutil
import tempfile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)


def download_file(url: str, folder: str) -> str:
    """Download a single file to the given folder and return the local path."""
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


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        download_resources = request.form.get('resources') == 'on'
        if not url:
            return render_template('download.html', error='No URL provided')
        if not urlparse(url).scheme:
            url = 'http://' + url

        temp_dir = tempfile.mkdtemp()
        try:
            resp = requests.get(url)
            resp.raise_for_status()

            html_path = os.path.join(temp_dir, 'page.html')
            with open(html_path, 'w', encoding=resp.encoding or 'utf-8') as f:
                f.write(resp.text)

            if download_resources:
                soup = BeautifulSoup(resp.text, 'html.parser')
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
                        download_file(res_url, temp_dir)
                    except Exception:
                        pass

            zip_path = shutil.make_archive(temp_dir, 'zip', temp_dir)
            return send_file(zip_path, as_attachment=True, download_name='webpage.zip')
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    return render_template('download.html')


if __name__ == '__main__':
    app.run(debug=True)
