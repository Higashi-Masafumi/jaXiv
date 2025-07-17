# arxivのidを受け取ってソースをダウンロードして翻訳を実行します

## ローカル開発環境のセットアップ
1. 仮想環境の構築
```
$ pip install uv
$ uv sync
```
2. fastapiサーバー起動
```
$ uvicron main:app --reload
```

## Docker環境のセットアップ
バックエンドではtex環境が必要になるので、`texlive-full`のインストールが必要になります。
しかし、このインストールには通常20分程度かかってしまいますいます。このプロジェクトでは`texlive-full`をベースイメージとして一度ビルドしてしまうことで、その後のbuildの時間を短縮します。

1. まずは`texlive-full`と`uv`が入ったベースイメージを[Dockerfile.base](Dockerfile.base)を使ってビルドします。
    ```bash
    $ docker build \
        -f Dockerfile.base \
        -t backend-base:local \
        backend
    ```
2. 次にベースイメージを元にバックエンドをビルドします。
    ```bash
    $ docker build \
        -f backend/Dockerfile \
        --build-arg BASE_IMAGE_URL=backend-base:local
        -t jaxiv-backend:dev
        backend
    ```

3. イメージをrunする
    ```bash
    $ docker run --rm -it \
        -p 8000:8000 \
        -v $(pwd):/app \
        jaxiv-backend:dev \
    ```
