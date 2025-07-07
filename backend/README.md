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
1. Dockerイメージのビルド
```
$ docker build -t jaxiv .
```
2. Hot ReloadしながらDocker run
```
$ docker run -it --rm \
    -v $(pwd):/app \
    -p 8000:8000 \
    jaxiv
```