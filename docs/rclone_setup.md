# rclone セットアップ手順

このプロジェクトでは、`rclone` を使用して Google Drive とローカルマシン間で音声ファイルを同期します。
以下の手順に従って、`rclone` のインストールと設定を行ってください。

## 1. rclone のインストール

お使いのOSに合った方法で `rclone` をインストールします。

### Windows

1.  [rcloneのダウンロードページ](https://rclone.org/downloads/)にアクセスします。
2.  "Intel/AMD - 64 Bit"向けの `.zip` ファイルをダウンロードします。
3.  zipファイルを解凍し、中にある `rclone.exe` をパスの通ったディレクトリ（例: `C:\rclone`）に配置し、そのディレクトリをシステムの環境変数 `Path` に追加します。

または、[Scoop](https://scoop.sh/) や [Chocolatey](https://chocolatey.org/) といったパッケージマネージャーを使うこともできます。
```powershell
# Scoopの場合
scoop install rclone

# Chocolateyの場合
choco install rclone
```

### macOS / Linux (WSL)

パッケージマネージャーを使用するのが最も簡単です。

```bash
# macOS (Homebrew)
brew install rclone

# Debian/Ubuntu/WSL(Debian or Ubuntu)
sudo apt-get update
sudo apt-get install rclone

# Fedora/CentOS
sudo yum install rclone
```
ターミナルで `rclone --version` を実行し、バージョン情報が表示されればインストールは成功です。

## 2. Google Drive リモートの設定

次に、Google Driveに接続するための `rclone` の設定（リモート）を行います。

1.  ターミナルまたはコマンドプロンプトを開き、以下のコマンドを実行します。
    ```
    rclone config
    ```

2.  対話形式の設定が始まります。以下の順で入力してください。
    *   `n) New remote` -> **n** と入力してEnter
    *   `name>` -> **gdrive** と入力してEnter（※スクリプトがこの名前を前提としています）
    *   `Type of storage to configure.` -> **drive** (Google Drive) の番号を探して入力
    *   `Google Application Client Id` -> そのままEnter（空欄）
    *   `Google Application Client Secret` -> そのままEnter（空欄）
    *   `scope>` -> **1** (`Full access all files, excluding Application Data Folder.`) を入力。もし読み取り専用でよければ `drive.readonly` の番号を入力します。
    *   `root_folder_id>` -> そのままEnter
    *   `service_account_file>` -> そのままEnter
    *   `Edit advanced config?` -> **n** (No) と入力
    *   `Use auto config?` -> **y** (Yes) と入力
        *   この時点で、ブラウザが自動的に開き、Googleアカウントの認証画面が表示されます。
        *   `rclone` がアクセスするGoogleアカウントを選択し、アクセスを許可してください。
        *   成功すると、ブラウザに "Success!" と表示され、ターミナルに認証コードが自動で貼り付けられます。
    *   `Configure this as a team drive?` -> **n** (No) と入力
    *   `y/e/d> y) Yes this is OK` -> **y** と入力
    *   `q) Quit config` -> **q** と入力して設定を終了します。

## 3. 設定の確認

以下のコマンドで、設定したリモート (`gdrive:`) のルートディレクトリにあるファイルとフォルダ一覧が表示されるか確認します。

```
rclone lsd gdrive:
```

一覧が表示されれば、設定は成功です。これで `scripts/sync_drive.sh` や `scripts/sync_drive.ps1` を実行する準備が整いました。
