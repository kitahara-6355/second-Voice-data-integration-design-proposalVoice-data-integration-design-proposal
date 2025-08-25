# 外部サービス連携ガイド

このドキュメントでは、本プロジェクトと外部サービスを連携させるための設定手順について説明します。

## 1. SlackへのCI/CD結果通知

GitHub Actionsで実行されるCI/CDの結果を、指定したSlackチャンネルにリアルタイムで通知することができます。

### 目的
- **CI/CDの結果通知:** `main`ブランチへのpushやPull Requestの作成時に実行されるテストの結果を、チームですばやく共有します。
- **パイプライン失敗通知:** ローカルで実行する自動化パイプライン (`run_pipeline.py`) でエラーが発生した際に、失敗したステップやエラー内容を即座に通知します。
- これらにより、システムの健全性を常に把握し、問題があれば迅速に対応できます。

### 設定手順

設定は、**Slack側でのWebhook URLの取得**と、**GitHub側でのSecret登録**の2つのステップで完了します。

#### ステップ 1: SlackでIncoming Webhook URLを取得する

1.  **Slackアプリの作成:**
    - [Slack API](https://api.slack.com/apps) にアクセスし、「Create New App」ボタンをクリックします。
    - 「From scratch」を選択し、アプリ名（例: `GitHub CI Notifier`）と、通知を投稿したいSlackワークスペースを選択して、「Create App」をクリックします。

2.  **Incoming Webhooksの有効化:**
    - 作成したアプリの管理画面で、左側のメニューから「Incoming Webhooks」を選択します。
    - 「Activate Incoming Webhooks」のトグルを「On」にします。

3.  **Webhook URLの生成:**
    - 同じページの下部にある「Add New Webhook to Workspace」ボタンをクリックします。
    - 通知を投稿したいチャンネルを選択し、「許可する」 (Allow) をクリックします。
    - これで、`https://hooks.slack.com/services/T.../B.../...` という形式の **Webhook URL** が生成されます。このURLをコピーしておきます。**このURLは外部に漏れないように厳重に管理してください。**

#### ステップ 2: GitHubリポジトリにSecretを登録する

1.  **リポジトリのSettingsに移動:**
    - このGitHubリポジトリのページで、「Settings」タブをクリックします。

2.  **Secretの作成:**
    - 左側のメニューから「Secrets and variables」>「Actions」を選択します。
    - 「New repository secret」ボタンをクリックします。
    - **Name** の欄に、必ず `SLACK_WEBHOOK_URL` と入力します。
    - **Secret** の欄に、ステップ1でコピーしたSlackのWebhook URLを貼り付けます。
    - 「Add secret」ボタンをクリックして保存します。

以上で設定は完了です。
次回以降、GitHub ActionsのCIワークフローが実行されるたびに、結果が指定したSlackチャンネルに自動で通知されるようになります。
