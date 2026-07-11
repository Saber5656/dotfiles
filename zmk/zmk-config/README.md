# zmk-config

`~/dev/dotfiles` で管理するための ZMK 設定実体です。
ZMK workspace 側の `config/zmk-config` から参照して使います。

想定例:

```bash
ln -s ~/dev/dotfiles/zmk/zmk-config ~/dev/zmk-workspace/config/zmk-config
```

## 構成

- `build.yaml`: Eyelash Corne 左右と `settings_reset` のビルド定義
- `config/west.yml`: vendor board を取得する west manifest
- `config/eyelash_corne.keymap`: 実運用 keymap
- `config/eyelash_corne.conf`: 実運用 Kconfig

## 次にやること

1. ZMK workspace で `just init config/zmk-config` を実行する
2. `nix develop` 後に left / right / `settings_reset` をビルドする
3. 実機更新後は Studio 保存設定との差分を必要に応じて整理する
