# dotfiles

設定ファイル・キーバインド・エージェント実行環境の設定を一元管理するリポジトリ。
実体をここに置き、各ツールが参照する場所からシンボリックリンクで接続する。

skill 本体は別 repository の `skills` を正本とし、この repository では dotfiles と runtime 設定だけを扱う。

## 管理対象

| dotfiles のパス | リンク先 |
|---|---|
| `COMMON-AGENTS.md` | `~/.claude/CLAUDE.md` と `~/.codex/AGENTS.md` が参照する共通 runtime instructions |
| `Brewfile` | Homebrew Bundle |
| `.cursorignore` | Cursor ignore 設定 |
| `bash/bashrc` | `~/.bashrc` |
| `zsh/zshrc` | `~/.zshrc` |
| `zsh/zprofile` | `~/.zprofile` |
| `starship/starship.toml` | `~/.config/starship.toml` |
| `git/ignore` | `~/.config/git/ignore` |
| `fish/config.fish` | `~/.config/fish/config.fish` |
| `karabiner/karabiner.json` | `~/.config/karabiner/karabiner.json` |
| `linermouse/linearmouse.json` | `~/.config/linearmouse/linearmouse.json` |
| `nvim/` | `~/.config/nvim/`（init.lua および lua/ 以下） |
| `tmux/tmux.conf` | `~/.tmux.conf` |
| `obsidian/hotkeys.json` | Obsidian hotkey settings |
| `wezterm/wezterm.lua` | `~/.config/wezterm/wezterm.lua` |
| `wezterm/keybind.lua` | `~/.config/wezterm/keybind.lua` |
| `zed/keymap.json` | `~/.config/zed/keymap.json` |
| `claude/settings.json` | `~/.claude/settings.json` |
| `claude/keybindings.json` | `~/.claude/keybindings.json` |
| `zmk/zmk-config/` | ZMK keyboard config |

Claude と Codex に実際に読ませる runtime instructions の SSOT は `COMMON-AGENTS.md` とし、
`~/.claude/CLAUDE.md` と `~/.codex/AGENTS.md` はこのファイルを参照する。

## エージェント共通ルール管理

- ドメイン固有の運用は各スキルや専用ドキュメントに寄せ、`COMMON-AGENTS.md` には最小限の共通ルールを置く
- Claude/Codex に実際に読ませるファイルは `COMMON-AGENTS.md` とし、これを SSOT として手動管理する
- skill 本体や skill 固有の references は `skills` repository 側で管理する
- transitional hook や runtime generated state はこの repository の管理対象にしない

### 起動ルールの更新

Claude/Codex の振る舞いを変えたいときは `COMMON-AGENTS.md` を直接編集する。

### primary checkout に別作業がある場合の配布

source の正本はこの repository の main 上の `COMMON-AGENTS.md` とする。
通常は上記 symlink で読み込む。primary に別 branch や未コミット変更がある場合は、
primary を checkout・reset・stash せず、マージ済み commit の COMMON だけを
バージョン付き配布先へ取り出して利用できる。

1. 配布する merge SHA と COMMON の blob/digest を固定する。
2. `git show <merge-SHA>:COMMON-AGENTS.md` で内容を取得し、Git 管理外の
   `~/.codex/policy-releases/dotfiles/<merge-SHA>/COMMON-AGENTS.md` に保存する。
   既存ファイルがあれば上書きせず内容一致を確認する。
3. `~/.codex/AGENTS.md` と `~/.claude/CLAUDE.md` の現在の symlink 先を記録する。
   実ファイルや予期しない変更があれば上書きせず、その差分を保持する。
4. 両リンクが確認した preimage のままであることを再確認し、同一ディレクトリの
   一時 symlink から rename して、配布先へ一つずつ切り替える。
   複数リンクの切替は一括 atomic ではないため、途中失敗では成功したリンクを記録し、
   今回設定した先から変わっていない場合だけ元のリンクへ戻す。
5. 両入口の実読込先と内容 digest を確認し、配布 SHA・リンク・結果を簡潔に記録する。
   既に動いている session への反映は推測せず、新しい task で読込を確認する。

配布 copy は編集元にしない。次回も main の検証済み SHA から更新する。
primary の別作業とその index は変更せず、過去の配布版も削除しない。

## セットアップ

新しい環境でシンボリックリンクを張り直す場合は、上記の対応表を参照して `ln -s` で作成する。

```bash
# 例
DOTFILES_DIR="$HOME/dev/dotfiles"

ln -sfn "$DOTFILES_DIR/COMMON-AGENTS.md" "$HOME/.claude/CLAUDE.md"
ln -sfn "$DOTFILES_DIR/COMMON-AGENTS.md" "$HOME/.codex/AGENTS.md"
ln -sfn "$DOTFILES_DIR/zsh/zshrc" "$HOME/.zshrc"
ln -sfn "$DOTFILES_DIR/zsh/zprofile" "$HOME/.zprofile"
ln -sfn "$DOTFILES_DIR/claude/settings.json" "$HOME/.claude/settings.json"
ln -sfn "$DOTFILES_DIR/claude/keybindings.json" "$HOME/.claude/keybindings.json"
```

## 管理対象外

以下は機密情報または実行時の自動生成ファイルのため管理しない。

- `~/.gitconfig` — メールアドレス等の個人情報を含む
- `~/.ssh/` — 秘密鍵
- `.claude/settings.json` — local Claude project settings
- `~/.claude/settings.local.json` — ローカル固有設定（APIキー等の可能性）
- `~/.config/mcp/` — OAuthシークレット等の認証情報
- `~/.claude/history.jsonl`、`~/.codex/history.jsonl` — 会話履歴
- `agents/agents.md`、`agents/base/common.md` — legacy agent entrypoint
- `claude/hooks/` — transitional Saihai / ITB runtime hooks
- `claude/plugins/installed_plugins.json`、`claude/plugins/known_marketplaces.json` — generated plugin state
- `claude/team-config.md` — deprecated compatibility stub
- `codex/config.toml`、`.codex/config.toml` — local Codex settings
- `codex/hooks.json`、`codex/hooks/`、`codex/bin/archive-shutdown` — transitional Codex hook runtime
- `nvim/lazyvim.json` — generated LazyVim state
- `zsh/local.zsh` — local/private shell additions
