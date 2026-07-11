-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here
-- NvimTree toggle
-- ~/.config/nvim/lua/config/keymaps.lua

-- 1) 既存の Explorer 系の割り当てを潰して、NvimTreeに統一する
-- LazyVim では <leader>e / <leader>E / E に何かしら入っていることが多いので、先に削除してから上書きする
pcall(vim.keymap.del, "n", "E")
pcall(vim.keymap.del, "n", "<leader>e")
pcall(vim.keymap.del, "n", "<leader>E")
pcall(vim.keymap.del, "n", "<leader>ee")

-- あなたが望む「NvimTree のエクスプローラ」だけを出す
vim.keymap.set("n", "E", "<cmd>NvimTreeToggle<CR>", { desc = "Toggle NvimTree" })
vim.keymap.set("n", "<leader>ee", "<cmd>NvimTreeToggle<CR>", { desc = "Toggle NvimTree" })
vim.keymap.set("n", "<leader>e", "<cmd>NvimTreeFocus<CR>", { desc = "Focus NvimTree" })

-- 2) NvimTree 内で n で新規作成できない問題の対処
-- NvimTree はデフォルトだと新規作成が 'a' のことが多い。
-- でもあなたは n で作りたい（/あるいは n が死んで困っている）ので、FileType=NvimTree の時だけ n を create に割り当てる。
vim.api.nvim_create_autocmd("FileType", {
  pattern = "NvimTree",
  callback = function(args)
    local ok, api = pcall(require, "nvim-tree.api")
    if not ok then
      return
    end

    -- バッファローカルに割り当て（他の通常バッファの 'n' には一切影響させない）
    vim.keymap.set(
      "n",
      "n",
      api.fs.create,
      { buffer = args.buf, nowait = true, silent = true, desc = "New file (NvimTree)" }
    )
  end,
})
