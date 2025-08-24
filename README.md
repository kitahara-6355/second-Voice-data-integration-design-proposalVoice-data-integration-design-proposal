# PixelRecordings-Analytics

## 概要

**PixelRecordings-Analytics** は、Google Pixel レコーダーで録音された会議音声を活用し、横断的な分析を可能にするためのデータパイプライン・プロジェクトです。

音声の文字起こしやベクトル化といった重い処理はプライバシーを重視してローカルで完結させ、メタデータや要約をクラウドに同期することで、スマートフォンなどから手軽に内容を確認できる仕組みの構築を目指します。

## ✨ 主な機能

- **ローカル処理パイプライン**: `rclone`でのファイル同期、`whisper.cpp`での文字起こし、`sentence-transformers`でのベクトル化、`ChromaDB`への登録までの一連の処理をスクリプトで実行。
- **検索API**: `FastAPI`で構築されたローカルAPIを通じて、ベクトル検索（類似文章検索）が可能。
- **クラウド連携**: 会議のメタデータや要約を`Google Firestore`や`Notion`に同期。
- **モバイル対応UI**: `Firebase Hosting`でホストされたPWA（Progressive Web App）で、どこからでも会議の要約を閲覧。

## 📖 ドキュメント

このプロジェクトを最大限に活用するために、以下のドキュメントを参照してください。

| ドキュメント                                       | 説明                                                                 |
| -------------------------------------------------- | -------------------------------------------------------------------- |
| 🚀 **[セットアップガイド](./docs/setup.md)**       | **最初にここから！** 開発環境をゼロから構築するための手順。          |
| 🏃 **[運用マニュアル (Runbook)](./docs/runbook.md)** | 日常的に新しい会議データを処理するためのステップバイステップの手順。 |
| 🧪 **[テスト実行ガイド](./docs/testing.md)**       | LintやE2Eテストなど、プロジェクトの品質を保つためのテスト実行方法。  |
| 🔗 **[外部サービス連携](./docs/integrations.md)**   | Slack通知など、外部サービスとの連携設定。                            |
| ☁️ **[rclone セットアップ](./docs/rclone_setup.md)** | Google Driveと同期するための`rclone`の具体的な設定方法。             |
| 📓 **[Notionスキーマ定義](./notion/notion_schema.md)** | Notionで利用を推奨するデータベースの構成案。                         |

## 🛠️ 主要コンポーネント

### ローカル (Windows/macOS/Linux)
- `rclone`: Google Drive ↔ ローカル同期
- `whisper.cpp`: 高速な文字起こし
- `sentence-transformers`: テキストの埋め込みベクトル生成
- `ChromaDB`: ベクトルストア
- `FastAPI`: ローカル検索API

### クラウド（無料枠想定）
- `Google Drive`: 音声ファイルのストレージ
- `Firebase Hosting`: PWAの配信
- `Firestore`: 会議メタデータ・要約の格納
- `Notion`: 課題・振り返り管理

---
*This project is currently under development.*
