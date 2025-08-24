# 運用マニュアル (Runbook)

## 🎯 このマニュアルの目的
このドキュメントは、`PixelRecordings-Analytics` プロジェクトの日常的な運用手順を、**初めて操作する方でも迷わず実行できること**を目標に説明します。

新しい会議の録音データをシステムに取り込み、分析・閲覧可能な状態にするまでの一連の流れを、具体的なコマンド例と共にステップバイステップで解説します。

## ✅ 1. 始める前に (前提条件)
このマニュアルを実行する前に、**[プロジェクトセットアップガイド](./setup.md)** の手順がすべて完了している必要があります。

特に、以下の点が満たされているか確認してください。
- ✅ Python, rclone, whisper.cpp などのソフトウェアがインストール済み
- ✅ Pythonの依存関係がインストール済み (`pip install -r ...`)
- ✅ Firebase と Notion の認証情報が正しく設定済み

## ⚙️ 2. 日常の運用ワークフロー
新しい会議データを処理する際は、以下の手順を順番に実行します。
各コマンドは、プロジェクトのルートディレクトリで実行してください。

---

### ステップ 1: Google Driveから音声ファイルを同期

**目的:** スマートフォンから自動でGoogle Driveにアップロードされた新しい録音ファイルを、分析のために手元のPCにダウンロードします。

- **Windows の場合 (PowerShell):**
  ```powershell
  .\scripts\sync_drive.ps1
  ```
- **Linux / macOS / WSL の場合 (Bash):**
  ```bash
  ./scripts/sync_drive.sh
  ```
**期待される結果:**
`local_data/recordings` ディレクトリに、Google Driveにあった新しい音声ファイルが追加されます。コンソールに同期の進捗が表示され、「Sync complete」というメッセージが出力されます。

---

### ステップ 2: 新しい音声ファイルを文字起こし

**目的:** ダウンロードした音声ファイル（例: `.m4a`）を、中身が読めるテキスト形式（JSON）に変換します。

`local_data/recordings` にあるファイルのうち、まだ処理していないもの（`local_data/transcripts` に対応するJSONファイルがないもの）を対象に実行します。

**例:** `meeting_A.m4a` というファイル1つを処理する場合

- **Windows (PowerShell):**
  ```powershell
  .\scripts\transcribe_whisper.ps1 -InputFile "local_data\recordings\meeting_A.m4a"
  ```
- **Linux / macOS / WSL (Bash):**
  ```bash
  ./scripts/transcribe_whisper.sh "local_data/recordings/meeting_A.m4a"
  ```

<details>
<summary>💡 **ヒント: 新しいファイルが複数ある場合**</summary>

毎回1つずつコマンドを打つ代わりに、簡単なループ処理を使うと便利です。

- **Windows (PowerShell):**
  ```powershell
  # local_data/recordings にある .m4a ファイルをすべて処理する例
  Get-ChildItem -Path "local_data\recordings" -Filter *.m4a | ForEach-Object {
      $transcriptPath = "local_data\transcripts\$($_.BaseName).json"
      if (-not (Test-Path $transcriptPath)) {
          Write-Host "Processing $($_.FullName)..."
          .\scripts\transcribe_whisper.ps1 -InputFile $_.FullName
      }
  }
  ```

- **Linux / macOS / WSL (Bash):**
  ```bash
  # local_data/recordings にある .m4a ファイルをすべて処理する例
  for f in local_data/recordings/*.m4a; do
    BASENAME=$(basename "$f" .m4a)
    if [ ! -f "local_data/transcripts/$BASENAME.json" ]; then
      echo "Processing $f..."
      ./scripts/transcribe_whisper.sh "$f"
    fi
  done
  ```
</details>

**期待される結果:**
`local_data/transcripts/` ディレクトリに、処理した音声ファイルと同名の `.json` ファイル（例: `meeting_A.json`）が生成されます。

---

### ステップ 3 & 4: データ登録とクラウド同期

**目的:** 生成されたJSONファイルの内容を、検索用データベース (ChromaDB) と、閲覧用のクラウドサービス (Firestore, Notion) の両方に登録します。

このステップも、新しいJSONファイルごとに実行します。

**例:** `meeting_A.json` というファイル1つを処理する場合

```bash
# 1. ChromaDBへの登録 (OS共通)
python scripts/embed_and_upsert.py --input "local_data/transcripts/meeting_A.json"

# 2. Firestoreへの同期 (OS共通)
python scripts/sync_to_firestore.py "local_data/transcripts/meeting_A.json"

# 3. Notionへの同期 (OS共通)
python scripts/sync_to_notion.py "local_data/transcripts/meeting_A.json"
```

<details>
<summary>💡 **ヒント: 新しいJSONが複数ある場合**</summary>

ここでもループが使えます。

- **Windows (PowerShell):**
  ```powershell
  Get-ChildItem -Path "local_data\transcripts" -Filter *.json | ForEach-Object {
      # ここではすでに処理済みかどうかのチェックは簡略化しています
      Write-Host "Syncing $($_.FullName)..."
      python scripts\embed_and_upsert.py --input $_.FullName
      python scripts\sync_to_firestore.py $_.FullName
      python scripts\sync_to_notion.py $_.FullName
  }
  ```

- **Linux / macOS / WSL (Bash):**
  ```bash
  for f in local_data/transcripts/*.json; do
    echo "Syncing $f..."
    python scripts/embed_and_upsert.py --input "$f"
    python scripts/sync_to_firestore.py "$f"
    python scripts/sync_to_notion.py "$f"
  done
  ```
</details>

**期待される結果:**
- `local_env/chroma_db` のデータベースが更新されます。
- Firestoreの `meetings` コレクションにドキュメントが作成・更新されます。
- Notionのデータベースに新しいページが作成され、そのURLがコンソールに表示されます。

---

### ステップ 5: Webアプリで確認

**目的:** 同期したデータが、スマートフォンやPCのブラウザから正しく閲覧できるか最終確認します。

1.  **Firebase Hostingにデプロイ:**
    (※Webアプリのコードを変更した場合のみ実行が必要です。通常は一度だけでOK)
    ```bash
    firebase deploy --only hosting
    ```
2.  **アプリを開く:**
    デプロイ時に表示される **Hosting URL** にブラウザでアクセスします。
3.  **確認:**
    - 新しい会議が一覧の先頭に表示されているか。
    - クリックすると、要約や全文が表示されるか。

## ❓ 4. トラブルシューティング
問題が発生した場合は、まず **[テスト実行ガイド](./testing.md)** を参照して、各コンポーネントが正しく動作するか確認してください。それでも解決しない場合は、以下の点を確認してください。

- **問題:** `rclone` コマンドが失敗する。
  - **解決策:** `rclone config` を実行して `gdrive` リモートが正しく設定されているか確認してください。Google Driveの認証が切れている場合は、再設定が必要です。

- **問題:** `whisper.cpp` が見つからないというエラーが出る。
  - **解決策:** `scripts/transcribe_whisper.sh` (または `.ps1`) 内の `WHISPER_CPP_DIR` のパスが正しいか確認してください。また、`whisper.cpp` が正しくビルドされているか確認してください。

- **問題:** FirestoreやNotionへの同期が認証エラーで失敗する。
  - **解決策 (Firestore):** `serviceAccountKey.json` のパスが正しいか、有効なキーであるか確認してください。
  - **解決策 (Notion):** 環境変数 `NOTION_API_TOKEN` と `NOTION_DATABASE_ID` が正しく設定されているか確認してください。

- **問題:** Webアプリに会議が表示されない。
  - **解決策:**
    1.  ブラウザの開発者ツール（F12キー）のコンソールにエラーが出ていないか確認します。
    2.  Firebaseコンソールで、Firestoreの `meetings` コレクションにデータが正しく存在するか確認します。
    3.  `firebase/hosting/js/app.js` 内の `firebaseConfig` が、ご自身のプロジェクトのものに正しく置き換えられているか確認します。
