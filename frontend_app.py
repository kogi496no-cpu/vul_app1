from flask import Flask, request, Response, render_template, jsonify
import requests
from lxml import etree
from urllib.parse import urlparse
from bs4 import BeautifulSoup

app = Flask(__name__)

# トップページ
@app.route('/')
def index():
    return render_template('index.html')

# SSRFチャレンジページ
@app.route('/ssrf')
def ssrf_page():
    return render_template('ssrf.html')

# サンプルページ
@app.route('/sample')
def sample_page():
    return render_template('sample_page.html')

# SSRF脆弱性を持つエンドポイント (OGPプレビュー)
@app.route('/fetch')
def fetch():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "Please provide a 'url' parameter."}), 400

    try:
        parsed_url = urlparse(url)
        
        if parsed_url.scheme in ['http', 'https']:
            headers = {'User-Agent': 'Mozilla/5.0 (compatible; GeminiBot/1.0; +http://www.google.com/bot.html)'}
            res = requests.get(url, timeout=5, headers=headers)
            res.raise_for_status()

            content_type = res.headers.get('content-type', '').lower()
            if 'text/html' in content_type:
                soup = BeautifulSoup(res.text, 'html.parser')
                ogp_data = {
                    'original_url': url,
                    'title': None,
                    'description': None,
                    'image': None,
                }
                title_tag = soup.find('meta', property='og:title')
                if title_tag and title_tag.get('content'):
                    ogp_data['title'] = title_tag.get('content')
                else:
                    title_tag = soup.find('title')
                    if title_tag and title_tag.string:
                        ogp_data['title'] = title_tag.string
                desc_tag = soup.find('meta', property='og:description')
                if desc_tag and desc_tag.get('content'):
                    ogp_data['description'] = desc_tag.get('content')
                image_tag = soup.find('meta', property='og:image')
                if image_tag and image_tag.get('content'):
                    ogp_data['image'] = image_tag.get('content')
                return jsonify(ogp_data)
            else:
                return Response(res.text, mimetype='text/plain')

        elif parsed_url.scheme == 'file':
            with open(parsed_url.path, 'r') as f:
                return Response(f.read(), mimetype='text/plain')
        else:
            return Response(f"Unsupported scheme: {parsed_url.scheme}", mimetype='text/plain', status=400)
            
    except requests.exceptions.RequestException as e:
        return Response(f"URLの取得中にエラーが発生しました: {e}", mimetype='text/plain', status=500)
    except Exception as e:
        return Response(f"予期せぬエラーが発生しました: {e}", mimetype='text/plain', status=500)

# XXE脆弱性を持つエンドポイント
@app.route('/upload-xml', methods=['POST'])
def upload_xml():
    xml_data = request.data
    if not xml_data:
        return "Please post XML data.", 400

    try:
        parser = etree.XMLParser(resolve_entities=True)
        doc = etree.fromstring(xml_data, parser)
        return f"Root element is: {doc.tag}"
    except etree.XMLSyntaxError as e:
        return f"Invalid XML: {e}", 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
