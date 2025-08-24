# 運用マニュアル (Runbook)

このドキュメントは、`PixelRecordings-Analytics` プロジェクトの日常的な運用手順を説明するものです。
新しい会議の録音データをシステムに取り込み、分析・閲覧可能な状態にするまでの一連の流れをステップバイステップで解説します。

## 1. 概要

このシステムの運用は、以下の5つの主要なステップで構成されます。

1.  **同期**: Google Drive に保存された新しい録音ファイルをローカルマシンにダウンロードします。
2.  **文字起こし**: ダウンロードした音声ファイルをテキストに変換し、JSONファイルとして保存します。
3.  **埋め込み**: 文字起こしされたテキストをベクトル化し、ローカルの検索データベース (ChromaDB) に登録します。
4.  **クラウド同期**: 会議のメタデータを Firestore と Notion にそれぞれ同期します。
5.  **確認**: Webアプリケーション (PWA) でデータが正しく表示されるか確認します。

## 2. 前提条件

このマニュアルの手順を実行する前に、お使いのコンピュータが以下の状態になっていることを確認してください。

### a. 必須ソフトウェア
- **Python 3.9+**: `python --version` で確認。
- **rclone**: `rclone --version` で確認。[セットアップ手順](./rclone_setup.md) に従って `gdrive` リモートが設定済みであること。
- **whisper.cpp**: `../whisper.cpp` ディレクトリにクローンされ、ビルド済みであること。
- **Git**: プロジェクトのソースコードを取得するために必要。
- **Firebase CLI**: (任意ですが推奨) `firebase --version` で確認。

### b. プロジェクト設定
1.  **リポジトリのクローン**:
    ```bash
    git clone <リポジトリのURL>
    cd PixelRecordings-Analytics
    ```
2.  **Python依存関係のインストール**:
    ```bash
    # プロジェクトルートで実行
    pip install -r scripts/requirements.txt
    pip install -r services/api/requirements.txt
    ```
3.  **Firebase サービスアカウントキー**:
    - `serviceAccountKey.json` という名前のキーファイルをプロジェクトのルートディレクトリに配置します。このファイルは `.gitignore` によりリポジトリには含まれません。
4.  **Notion APIキーの設定**:
    - `NOTION_API_TOKEN` と `NOTION_DATABASE_ID` を環境変数として設定します。[スキーマ定義](./notion_schema.md) を参照してデータベースIDを確認してください。

## 3. 日常の運用ワークフロー

新しい会議データを処理する際は、以下の手順を順番に実行します。
各コマンドは、プロジェクトのルートディレクトリで実行することを想定しています。

---

### ステップ 1: Google Driveから音声ファイルを同期

Google Drive に自動アップロードされた新しい録音ファイル（`.m4a`など）をローカルの `local_data/recordings` ディレクトリにダウンロードします。

- **Windows の場合 (PowerShell):**
  ```powershell
  .\scripts\sync_drive.ps1
  ```
- **Linux / macOS / WSL の場合 (Bash):**
  ```bash
  ./scripts/sync_drive.sh
  ```
**→ 結果:** `local_data/recordings` に新しい音声ファイルが追加されます。

---

### ステップ 2: 新しい音声ファイルを文字起こし

同期した音声ファイルのうち、まだ処理していないものを文字起こしします。

**例:** `meeting_20240823.m4a` というファイルが新しい場合

- **Windows の場合 (PowerShell):**
  ```powershell
  .\scripts\transcribe_whisper.ps1 -InputFile "local_data\recordings\meeting_20240823.m4a"
  ```
- **Linux / macOS / WSL の場合 (Bash):**
  ```bash
  ./scripts/transcribe_whisper.sh "local_data/recordings/meeting_20240823.m4a"
  ```
**→ 結果:** `local_data/transcripts/meeting_20240823.json` のようなJSONファイルが生成されます。
**※ 新しいファイルが複数ある場合は、ファイルごとにこのコマンドを繰り返してください。**

---

### ステップ 3: テキストを埋め込み、ChromaDBに登録

生成された文字起こしJSONファイルを読み込み、内容をベクトル化してローカルの検索データベースに登録します。

- **Windows / Linux / macOS共通:**
  ```bash
  python scripts/embed_and_upsert.py --input "local_data/transcripts/meeting_20240823.json"
  ```
**→ 結果:** `local_env/chroma_db` 内のデータベースが更新されます。
**※ JSONファイルごとにこのコマンドを繰り返してください。**

---

### ステップ 4: メタデータをクラウドに同期

メタデータをFirestoreとNotionにそれぞれ同期します。

#### a. Firestoreへの同期

- **Windows / Linux / macOS共通:**
  ```bash
  python scripts/sync_to_firestore.py "local_data/transcripts/meeting_20240823.json" --key "serviceAccountKey.json"
  ```
**→ 結果:** Firestoreの `meetings` コレクションにドキュメントが作成・更新されます。

#### b. Notionへの同期

- **Windows / Linux / macOS共通:**
  ```bash
  python scripts/sync_to_notion.py "local_data/transcripts/meeting_20240823.json"
  ```
**→ 結果:** Notionの指定したデータベースに新しいページが作成されます。
**※ JSONファイルごとにこれらのコマンドを繰り返してください。**

---

### ステップ 5: Webアプリで確認

1.  (初回のみ) Firebase HostingにPWAをデプロイします。
    ```bash
    firebase deploy --only hosting
    ```
2.  デプロイされたURL、またはローカルで `firebase emulators:start` を使ってWebアプリを開きます。
3.  新しい会議が一覧に表示され、クリックすると要約やトランスクリプトが閲覧できることを確認します。

## 4. トラブルシューティング

- **問題:** `rclone` コマンドが失敗する。
  - **解決策:** `rclone config` を実行して `gdrive` リモートが正しく設定されているか確認してください。Google Driveの認証が切れている場合は、再設定が必要です。

- **問題:** `whisper.cpp` が見つからないというエラーが出る。
  - **解決策:** `scripts/transcribe_whisper.sh` (または `.ps1`) 内の `WHISPER_CPP_DIR` のパスが正しいか確認してください。また、`whisper.cpp` が正しくビルドされているか確認してください。

- **問題:** `pip install` が失敗する。
  - **解決策:** Pythonのバージョンが古い可能性があります。3.9以上を推奨します。また、`torch` のインストールで問題が発生する場合は、[PyTorchの公式サイト](https://pytorch.org/)でご自身の環境に合ったインストールコマンドを確認してください。

- **問題:** FirestoreやNotionへの同期が認証エラーで失敗する。
  - **解決策 (Firestore):** `serviceAccountKey.json` のパスが正しいか、有効なキーであるか確認してください。
  - **解決策 (Notion):** 環境変数 `NOTION_API_TOKEN` と `NOTION_DATABASE_ID` が正しく設定されているか確認してください。また、Notionインテグレーションが対象のデータベースに招待されているか確認してください。

- **問題:** Webアプリに会議が表示されない。
  - **解決策:**
    1.  ブラウザの開発者コンソールを開き、エラーメッセージを確認してください。
    2.  Firestoreの `meetings` コレクションにデータが正しく存在するか、Firebaseコンソールで確認してください。
    3.  `js/app.js` 内のFirebase設定 (`firebaseConfig`) が、ご自身のプロジェクトのものに正しく置き換えられているか確認してください。
