# Notion データベーススキーマ定義

このプロジェクトで利用を推奨するNotionデータベースの構成案です。
これらのデータベースをNotionで作成し、リレーションで連携させることで、会議の記録からタスク管理、振り返りまでを一元管理できます。

---

## 1. Meetings （会議録）

会議のメタデータと要約を管理する中心的なデータベースです。

| プロパティ名      | タイプ         | 説明                                                              |
| ----------------- | -------------- | ----------------------------------------------------------------- |
| **Meeting Title** | `Title`        | 会議のタイトル（例: 「2024-08-23 定例会議」）                     |
| **Date**          | `Date`         | 会議の開催日。                                                    |
| **Tags**          | `Multi-select` | 会議のカテゴリ（例: 「定例」「プロジェクトA」「技術検討」）       |
| **Summary**       | `Text`         | 会議の要約。                                                      |
| **Participants**  | `Person`       | 会議の参加者（Notionユーザー）。または `Text` プロパティでも可。   |
| **Status**        | `Select`       | 会議の状態（例: 「計画中」「完了」「要確認」）                     |
| **Action Items**  | `Relation`     | 「Action Items」データベースへのリレーション。                    |
| **Retrospective** | `Relation`     | 「Retrospectives」データベースへのリレーション。                  |
| **Firestore ID**  | `Text`         | `sync_to_firestore.py` で使用される `meeting_id`。連携用に保持。 |
| **Created Time**  | `Created time` | ページの作成日時。                                                |

---

## 2. Action Items （タスク管理）

会議から発生した具体的なタスクを管理します。

| プロパティ名   | タイプ       | 説明                                           |
| -------------- | ------------ | ---------------------------------------------- |
| **Task**       | `Title`      | タスクの内容。                                 |
| **Meeting**    | `Relation`   | どの「Meetings」から発生したタスクかを示す。   |
| **Owner**      | `Person`     | タスクの担当者。                               |
| **Due Date**   | `Date`       | タスクの期日。                                 |
| **Status**     | `Select`     | タスクの進捗（例: 「未着手」「進行中」「完了」） |
| **Priority**   | `Select`     | 優先度（例: 「高」「中」「低」）               |

---

## 3. Retrospectives （振り返り）

会議ごとの振り返り（Keep, Problem, Tryなど）を記録します。

| プロパティ名             | タイプ     | 説明                                                         |
| ------------------------ | ---------- | ------------------------------------------------------------ |
| **Reflection Title**     | `Title`    | 振り返りのタイトル（例: 「2024-08-23 定例会議の振り返り」） |
| **Meeting**              | `Relation` | どの「Meetings」に対する振り返りかを示す。                   |
| **What Went Well (Keep)**| `Text`     | 良かった点、継続したいこと。                                 |
| **To Be Improved (Problem)** | `Text`     | 改善したい点、問題点。                                       |
| **Try**                  | `Text`     | 次に試すこと。                                               |

---

### セットアップ手順

1.  上記の定義に従って、ご自身のNotionワークスペースに3つのデータベースを作成します。
2.  `Meetings` データベースと他の2つのデータベース間で `Relation` プロパティを設定します。
3.  `sync_to_notion.py` を実行する際に、`Meetings` データベースの **Database ID** が必要になります。
    - Database IDは、データベースをフルページで開いたときのURL `https://www.notion.so/{workspace}/{database_id}?v=...` の `{database_id}` の部分です。
4.  Notionインテグレーションを作成し、**APIトークン** を取得します。
    - [https://www.notion.so/my-integrations](https://www.notion.so/my-integrations) から作成できます。
    - 作成したインテグレーションを、対象のデータベース（親ページ）で「招待」して権限を与える必要があります。
