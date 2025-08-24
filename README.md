# PixelRecordings-Analytics

## 概要

**プロジェクト名:** PixelRecordings-Analytics

**目的:** Pixel（Google Pixel レコーダー）で録音された会議音声をローカルで文字起こし（Whisper）、埋め込み生成（sentence-transformers）、ベクトル保存（Chroma / Qdrant）し、メタデータ／要約を Firestore / Notion に同期して、Firebase Hosting 上の PWA でスマホから閲覧できる仕組みを構築する。

**設計方針（MVP）**

* 個人利用を前提に『無料枠＋ローカル処理』で実装
* 音声の文字起こしと埋め込みはローカルで完結（プライバシー重視）
* メタ・要約は Firestore / Notion に保存してスマホで確認
* 開発は GitHub で管理、Jules に Issue を割り当てる

---

## 主要コンポーネント

**ローカル (Windows)**

* rclone: Google Drive ↔ ローカル同期
* Whisper / whisper.cpp: 文字起こし
* sentence-transformers: 埋め込み生成
* Chroma（または Qdrant via Docker）: ベクトルストア
* FastAPI: ローカル検索 API

**クラウド（無料枠想定）**

* Google Drive: ストレージ（既存の15GB）
* Firebase Hosting: PWA 配信
* Firestore: 会議メタ・要約の格納
* Notion: 課題・振り返り管理（無料プラン）

---

## セットアップ（開発者向け簡易）

### 前提

* Windows 10/11（WSL 可）
* Python 3.9+（venv 推奨）
* rclone インストール済み
* whisper.cpp のビルドが可能（CPU モードを想定）
* GitHub アカウント
* Firebase プロジェクト（無料枠）
* Notion API トークン

### 初期手順（ローカル）

1. リポジトリをクローン
   ```bash
   git clone <repo-url>
   cd PixelRecordings-Analytics
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r services/api/requirements.txt
   ```
2. rclone remote の設定（`rclone config`）で `gdrive` を作成
3. `scripts/sync_drive.ps1`（Windows）を編集し、remote/local パスを合わせて実行
4. whisper.cpp をビルドし、`scripts/transcribe_whisper.sh` を参考に文字起こし実行
5. `python scripts/embed_and_upsert.py local_data/transcripts/meetingA.json` で Chroma に登録
6. `python scripts/sync_to_firestore.py local_data/transcripts/meetingA.json` で Firestore にメタ同期
7. `firebase deploy`（hosting）で PWA をデプロイ

---

## 運用フロー（短期/手動）

1. Pixel → Google Drive（自動アップロード）
2. `scripts/sync_drive.ps1` を手動実行（またはタスクスケジューラ）
3. `scripts/transcribe_whisper.sh` を実行 → transcripts 出力
4. `scripts/embed_and_upsert.py` を実行 → Chroma に登録
5. `scripts/sync_to_firestore.py` を実行 → Firestore に要約/メタ登録
6. Firebase UI で確認

---

## 注意点

* 機密データはローカル処理を優先
* Firebase の書き込み/読み取りルールを適切に設定
* 大量データは Firestore にベクトルを保存しない（コスト増）
