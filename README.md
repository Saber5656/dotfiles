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
