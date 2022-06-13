# sh-mpd

webブラウザ上からmpdを操作できるCGIシェルスクリプト

## 開発の目標

### 高い移植性

- シェル固有の拡張機能の使用を廃し,様々なPOSIX準拠環境での動作を可能にする

- 可能な限りPOSIX準拠のコマンドを使用

- web uiをテキストブラウザを含むあらゆるブラウザでの動作できるようにする

### 低リソース

- ホスト,クライアント側共に少ないリソースで利用可能
