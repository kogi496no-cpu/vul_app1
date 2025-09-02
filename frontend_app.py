from flask import Flask, request, Response, render_template, jsonify, render_template_string
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

# XXE脆弱性を持つエンドポイント (SVGアップローダー)
@app.route('/xxe', methods=['GET', 'POST'])
def xxe_page():
    if request.method == 'POST':
        if 'svg_file' not in request.files:
            return render_template('xxe.html', error='ファイルが選択されていません。')
        
        file = request.files['svg_file']
        if file.filename == '':
            return render_template('xxe.html', error='ファイル名が空です。')

        if file and file.mimetype == 'image/svg+xml':
            try:
                svg_content = file.read()
                
                # XXE脆弱性を作り込むためのパーサー
                # resolve_entities=True がキモよ！
                parser = etree.XMLParser(resolve_entities=True)
                doc = etree.fromstring(svg_content, parser)
                
                # パースした内容を文字列として再度レンダリング
                # これで外部エンティティが展開された結果が表示される
                uploaded_svg = etree.tostring(doc, pretty_print=True).decode('utf-8')
                
                return render_template('xxe.html', uploaded_svg=uploaded_svg)
            except etree.XMLSyntaxError as e:
                return render_template('xxe.html', error=f'無効なSVGファイルです: {e}')
            except Exception as e:
                return render_template('xxe.html', error=f'予期せぬエラーが発生しました: {e}')
        else:
            return render_template('xxe.html', error='SVGファイルを選択してください。')

    return render_template('xxe.html')

# パーソナライズされたメッセージ表示機能 (SSTI脆弱性)
@app.route('/personalize', methods=['GET', 'POST'])
def personalize_page():
    if request.method == 'POST':
        name = request.form.get('name', '名無し')
        department = request.form.get('department', '所属不明')
        motto = request.form.get('motto', '')

        # mottoをテンプレートとしてレンダリング（SSTI脆弱性）
        rendered_motto = render_template_string(motto)

        # 結果をプロフィールカード風のHTMLで返す
        response_html = f"""
        <!DOCTYPE html>
        <html lang="ja">
        <head>
            <meta charset="UTF-8">
            <title>生成された紹介カード</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    background-color: #f8f9fa;
                }}
                .profile-card {{
                    max-width: 500px;
                    margin: 50px auto;
                    border: none;
                    border-radius: 15px;
                    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                }}
                .card-header {{
                    background-color: #343a40;
                    color: white;
                    font-weight: bold;
                    border-top-left-radius: 15px;
                    border-top-right-radius: 15px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="card profile-card text-center">
                    <div class="card-header py-3">
                        MEMBER PROFILE
                    </div>
                    <div class="card-body p-4">
                        <img src="/static/images/office.png" class="rounded-circle mb-3" alt="profile image" width="100">
                        <h3 class="card-title">{name}</h3>
                        <h5 class="card-subtitle mb-2 text-muted">{department}</h5>
                        <hr>
                        <p class="card-text fst-italic">" {rendered_motto} "</p>
                    </div>
                </div>
                <div class="text-center">
                    <a href="/personalize" class="btn btn-primary">もう一度作成</a>
                    <a href="/" class="btn btn-secondary">トップに戻る</a>
                </div>
            </div>
        </body>
        </html>
        """
        return response_html
    return render_template('personalize.html')

# SSTI脆弱性を持つエンドポイント
@app.route('/ssti')
def ssti_page():
    template = request.args.get('template', 'Hello, {{ name }}!')
    name = request.args.get('name', 'Guest')
    return render_template_string(template, name=name)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
