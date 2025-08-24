# プロジェクトセットアップガイド

このドキュメントでは、`PixelRecordings-Analytics` プロジェクトをローカルマシンで動作させるための詳細なセットアップ手順を説明します。

## 1. 必須ソフトウェアのインストール

### a. Git
バージョン管理システムです。プロジェクトのソースコードをダウンロードするために使用します。
- **Windows**: [git-scm.com](https://git-scm.com/download/win) からインストーラーをダウンロードしてインストールします。
- **macOS**: `xcode-select --install` をターミナルで実行するか、[Homebrew](https://brew.sh/) を使って `brew install git` を実行します。
- **Linux (Debian/Ubuntu)**: `sudo apt update && sudo apt install git` を実行します。

### b. Python
本プロジェクトのスクリプトは Python で書かれています。
- **推奨バージョン**: 3.9+
- **Windows**: [python.org](https://www.python.org/downloads/windows/) からインストーラーをダウンロードします。**インストール時に「Add Python to PATH」のチェックボックスを必ずオンにしてください。**
- **macOS**: Homebrew を使って `brew install python` を実行するのが簡単です。
- **Linux (Debian/Ubuntu)**: `sudo apt update && sudo apt install python3 python3-pip python3-venv` を実行します。

### c. rclone
Google Driveとのファイル同期に使用します。
- 詳細は [rclone セットアップ手順](./rclone_setup.md) を参照してください。`rclone config` を使って `gdrive` という名前のリモートを設定するまでを完了させてください。

### d. whisper.cpp
音声ファイルの文字起こしに使用する、C++で実装された高速なプログラムです。
1.  **リポジトリのクローン**: このプロジェクト(`PixelRecordings-Analytics`)と同じ階層のディレクトリにクローンするのがおすすめです。
    ```bash
    # PixelRecordings-Analytics と同じディレクトリで実行
    git clone https://github.com/ggerganov/whisper.cpp.git
    ```
2.  **ビルド**:
    ```bash
    cd whisper.cpp
    make
    ```
    これで `main` という実行ファイルが生成されます。
3.  **モデルのダウンロード**:
    ```bash
    # whisper.cpp ディレクトリ内で実行
    ./models/download-ggml-model.sh base.en
    ```
    `models/ggml-base.en.bin` というモデルファイルがダウンロードされます。

## 2. プロジェクトのセットアップ

### a. ソースコードの取得
```bash
git clone https://github.com/<your-username>/PixelRecordings-Analytics.git
cd PixelRecordings-Analytics
```

### b. Python仮想環境の構築と依存関係のインストール
仮想環境を作成することで、プロジェクトの依存関係がグローバル環境を汚さなくなります。

```bash
# 1. 仮想環境を作成
python -m venv .venv

# 2. 仮想環境を有効化
# Windows (Command Prompt)
# .venv\Scripts\activate.bat
# Windows (PowerShell)
# .venv\Scripts\Activate.ps1
# macOS / Linux
# source .venv/bin/activate

# 3. 依存関係をインストール
pip install --upgrade pip
pip install -r scripts/requirements.txt
pip install -r services/api/requirements.txt
```

### c. クラウドサービスの認証情報設定

#### Firebase
1.  [Firebase Console](https://console.firebase.google.com/) でプロジェクトを作成します。
2.  プロジェクト設定 > サービスアカウント に移動します。
3.  「新しい秘密鍵の生成」をクリックし、キーファイル（JSON形式）をダウンロードします。
4.  ダウンロードしたファイルを `serviceAccountKey.json` にリネームし、このプロジェクトのルートディレクトリ（`.gitignore`がある場所）に配置します。

#### Notion
1.  [Notionインテグレーションページ](https://www.notion.so/my-integrations)で新しいインテグレーションを作成します。
2.  作成したインテグレーションの「Secrets」タブから **Internal Integration Token** をコピーします。
3.  [スキーマ定義](./notion_schema.md) に従って作成したデータベースを、親ページごと、またはデータベースごとにインテグレーションに共有（招待）します。
4.  `Meetings` データベースのIDをURLから取得します (`https://www.notion.so/{workspace_name}/{database_id}?v=...` の `database_id` 部分)。
5.  取得したトークンとデータベースIDを**環境変数**として設定します。
    - **macOS / Linux**:
      ```bash
      export NOTION_API_TOKEN="secret_..."
      export NOTION_DATABASE_ID="..."
      # .bashrc や .zshrc に追記すると恒久的に設定できます。
      ```
    - **Windows (PowerShell)**:
      ```powershell
      $env:NOTION_API_TOKEN="secret_..."
      $env:NOTION_DATABASE_ID="..."
      # 恒久的に設定するには、システムのプロパティから環境変数を編集します。
      ```

これで、プロジェクトを実行するためのすべての準備が整いました。
次は [運用マニュアル (Runbook)](./runbook.md) に従って、実際のデータ処理を試してみてください。
