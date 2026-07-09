local wezterm = require("wezterm")
local act = wezterm.action
local tiled_window_slots = {}

local function cwd_path(pane)
	local cwd = pane:get_current_working_dir()
	return cwd and cwd.file_path or nil
end

-- tmuxが実行中かどうかを判定
local function is_tmux(pane)
	local process = pane:get_foreground_process_name() or ""
	return process:find("tmux") ~= nil
end

-- tmux実行中はキーをパススルー、それ以外はWezTermのペイン移動
local function pane_or_passthrough(direction, key)
	return wezterm.action_callback(function(window, pane)
		if is_tmux(pane) then
			window:perform_action(act.SendKey({ key = key, mods = "CTRL" }), pane)
		else
			window:perform_action(act.ActivatePaneDirection(direction), pane)
		end
	end)
end

-- Show which key table is active in the status area
wezterm.on("update-right-status", function(window, pane)
	local name = window:active_key_table()
	if name then
		name = "TABLE: " .. name
	end
	window:set_right_status(name or "")
end)

local function workspace_windows(workspace, current_window_id)
	local items = {}

	if not wezterm.gui then
		return items
	end

	for _, gui_win in ipairs(wezterm.gui.gui_windows()) do
		local mux_win = gui_win:mux_window()
		if mux_win and mux_win:get_workspace() == workspace then
			table.insert(items, {
				gui = gui_win,
				is_current = gui_win:window_id() == current_window_id,
			})
		end
	end

	table.sort(items, function(a, b)
		if a.is_current ~= b.is_current then
			return a.is_current
		end
		return a.gui:window_id() < b.gui:window_id()
	end)

	return items
end

local function four_window_geometry(screen, gap)
	local width = math.floor((screen.width - gap) / 2)
	local height = math.floor((screen.height - gap) / 2)

	local slots = {
		{ x = screen.x, y = screen.y },
		{ x = screen.x + width + gap, y = screen.y },
		{ x = screen.x, y = screen.y + height + gap },
		{ x = screen.x + width + gap, y = screen.y + height + gap },
	}

	return width, height, slots
end

local function remember_tiled_window_slots(workspace, items)
	local slots = {}

	for i = 1, math.min(4, #items) do
		local gui = items[i].gui
		if gui then
			slots[gui:window_id()] = i
		end
	end

	tiled_window_slots[workspace] = slots
end

local function adjacent_slot(slot, direction)
	if direction == "Left" then
		return ({ [2] = 1, [4] = 3 })[slot]
	end
	if direction == "Right" then
		return ({ [1] = 2, [3] = 4 })[slot]
	end
	if direction == "Up" then
		return ({ [3] = 1, [4] = 2 })[slot]
	end
	if direction == "Down" then
		return ({ [1] = 3, [2] = 4 })[slot]
	end
end

local function focus_window_in_direction(direction)
	return wezterm.action_callback(function(window, pane)
		if not wezterm.gui then
			return
		end

		local workspace = window:active_workspace()
		local slots = tiled_window_slots[workspace] or {}
		local current_slot = slots[window:window_id()]
		local target_slot = current_slot and adjacent_slot(current_slot, direction) or nil

		if target_slot then
			for _, gui_win in ipairs(wezterm.gui.gui_windows()) do
				local mux_win = gui_win:mux_window()
				if mux_win and mux_win:get_workspace() == workspace and slots[gui_win:window_id()] == target_slot then
					gui_win:focus()
					return
				end
			end
		end

		local delta = (direction == "Left" or direction == "Up") and -1 or 1
		window:perform_action(act.ActivateWindowRelativeNoWrap(delta), pane)
	end)
end

local function layout_four_windows(workspace, items, screen, gap)
	local width, height, slots = four_window_geometry(screen, gap)

	remember_tiled_window_slots(workspace, items)

	for i = 1, math.min(4, #items) do
		local gui = items[i].gui
		if gui then
			gui:restore()
			gui:set_position(slots[i].x, slots[i].y)
			gui:set_inner_size(width, height)
		end
	end
end

local function layout_workspace_windows(workspace, current_window_id, screen, gap, expected_count, retries_left)
	local items = workspace_windows(workspace, current_window_id)
	if #items >= expected_count or retries_left <= 0 then
		layout_four_windows(workspace, items, screen, gap)
		return
	end

	wezterm.time.call_after(0.1, function()
		layout_workspace_windows(workspace, current_window_id, screen, gap, expected_count, retries_left - 1)
	end)
end

return {
	keys = {
		{
			-- workspaceの切り替え
			key = "w",
			mods = "LEADER",
			action = act.ShowLauncherArgs({ flags = "WORKSPACES", title = "Select workspace" }),
		},
		{
			--workspaceの名前変更
			key = "$",
			mods = "LEADER",
			action = act.PromptInputLine({
				description = "(wezterm) Set workspace title:",
				action = wezterm.action_callback(function(win, pane, line)
					if line then
						wezterm.mux.rename_workspace(wezterm.mux.get_active_workspace(), line)
					end
				end),
			}),
		},
		{
			key = "W",
			mods = "LEADER|SHIFT",
			action = act.PromptInputLine({
				description = "(wezterm) Create new workspace:",
				action = wezterm.action_callback(function(window, pane, line)
					if line then
						window:perform_action(
							act.SwitchToWorkspace({
								name = line,
							}),
							pane
						)
					end
				end),
			}),
		},
		-- コマンドパレット表示
		{ key = "p", mods = "SUPER", action = act.ActivateCommandPalette },
		-- Tab移動
		{ key = "Tab", mods = "CTRL", action = act.ActivateTabRelative(1) },
		{ key = "Tab", mods = "SHIFT|CTRL", action = act.ActivateTabRelative(-1) },
		-- Tab入れ替え
		{ key = "{", mods = "CTRL", action = act({ MoveTabRelative = -1 }) },
		-- Tab新規作成
		{ key = "t", mods = "SUPER", action = act({ SpawnTab = "CurrentPaneDomain" }) },
		-- Tabを閉じる
		{ key = "w", mods = "SUPER", action = act({ CloseCurrentTab = { confirm = true } }) },
		{ key = "}", mods = "CTRL", action = act({ MoveTabRelative = 1 }) },

		-- 画面フルスクリーン切り替え
		--{ key = "Enter", mods = "CTRL", action = act.ToggleFullScreen },
		{
			key = "Enter",
			mods = "CTRL",
			action = wezterm.action_callback(function(window, pane)
				window:maximize()
			end),
		},

		-- Shift+Enterで改行（Claude Code等のマルチライン入力対応）
		{ key = "Enter", mods = "SHIFT", action = act.SendString("\x1b[13;2u") },

		-- スクロール
		{ key = "PageUp", mods = "SHIFT", action = act.ScrollByPage(-1) },
		{ key = "PageDown", mods = "SHIFT", action = act.ScrollByPage(1) },

		-- ターミナル内検索
		{ key = "f", mods = "SUPER", action = act.Search({ CaseSensitiveString = "" }) },

		-- QuickSelect（URL等を素早く選択）
		{ key = "Space", mods = "CTRL|SHIFT", action = act.QuickSelect },

		-- スクロールバック履歴クリア
		{ key = "k", mods = "SUPER", action = act.ClearScrollback("ScrollbackOnly") },

		-- コピーモード
		-- { key = 'X', mods = 'LEADER', action = act.ActivateKeyTable{ name = 'copy_mode', one_shot =false }, },
		{ key = "[", mods = "LEADER", action = act.ActivateCopyMode },
		-- コピー
		{ key = "c", mods = "SUPER", action = act.CopyTo("Clipboard") },
		-- 貼り付け
		{ key = "v", mods = "SUPER", action = act.PasteFrom("Clipboard") },

		-- Pane作成 Ctrl + Shift + hjkl（アクティブPaneから上下左右に分割）
		{ key = "h", mods = "CTRL|SHIFT", action = act.SplitPane({ direction = "Left", size = { Percent = 50 } }) },
		{ key = "j", mods = "CTRL|SHIFT", action = act.SplitPane({ direction = "Down", size = { Percent = 50 } }) },
		{ key = "k", mods = "CTRL|SHIFT", action = act.SplitPane({ direction = "Up", size = { Percent = 50 } }) },
		{ key = "l", mods = "CTRL|SHIFT", action = act.SplitPane({ direction = "Right", size = { Percent = 50 } }) },
		-- Paneを閉じる Ctrl + Shift + x
		{ key = "x", mods = "CTRL|SHIFT", action = act({ CloseCurrentPane = { confirm = true } }) },
		-- Pane移動 Ctrl + hjkl（tmux時はパススルー、それ以外はWezTermペイン移動）
		{ key = "h", mods = "CTRL", action = pane_or_passthrough("Left", "h") },
		{ key = "l", mods = "CTRL", action = pane_or_passthrough("Right", "l") },
		{ key = "k", mods = "CTRL", action = pane_or_passthrough("Up", "k") },
		{ key = "j", mods = "CTRL", action = pane_or_passthrough("Down", "j") },
		-- Window移動 Leader + Shift + hjkl
		{ key = "H", mods = "LEADER|SHIFT", action = focus_window_in_direction("Left") },
		{ key = "L", mods = "LEADER|SHIFT", action = focus_window_in_direction("Right") },
		{ key = "K", mods = "LEADER|SHIFT", action = focus_window_in_direction("Up") },
		{ key = "J", mods = "LEADER|SHIFT", action = focus_window_in_direction("Down") },
		-- Pane選択
		{ key = "[", mods = "CTRL|SHIFT", action = act.PaneSelect },
		-- 選択中のPaneのみ表示
		{ key = "z", mods = "CTRL", action = act.TogglePaneZoomState },
		-- 4つのwindowを2x2に整地
		{
			key = "q",
			mods = "LEADER",
			action = wezterm.action_callback(function(window, pane)
				if not wezterm.gui then
					return
				end

				local workspace = window:active_workspace()
				local screen = wezterm.gui.screens().active
				local gap = 8
				local current_window_id = window:window_id()
				local items = workspace_windows(workspace, current_window_id)
				local _, _, slots = four_window_geometry(screen, gap)

				if #items < 4 then
					for i = #items + 1, 4 do
						wezterm.mux.spawn_window({
							workspace = workspace,
							cwd = cwd_path(pane),
							position = {
								x = slots[i].x,
								y = slots[i].y,
								origin = "ScreenCoordinateSystem",
							},
						})
					end
				end

				layout_workspace_windows(workspace, current_window_id, screen, gap, 4, 10)
			end),
		},
		-- Pane分割を均等にリセット
		{
			key = "=",
			mods = "CTRL",
			action = wezterm.action_callback(function(window, pane)
				local tab = pane:tab()
				local panes = tab:panes_with_info()
				if #panes < 2 then
					return
				end
				-- 左右分割か上下分割かを判定
				local is_lr = panes[1].top == panes[2].top
				if is_lr then
					local total = 0
					for _, p in ipairs(panes) do
						total = total + p.width
					end
					local target = math.floor(total / #panes)
					for _, p in ipairs(panes) do
						if p.is_active then
							local diff = target - p.width
							if diff > 0 then
								local dir = p.left == 0 and "Right" or "Left"
								window:perform_action(act.AdjustPaneSize({ dir, diff }), pane)
							elseif diff < 0 then
								local dir = p.left == 0 and "Left" or "Right"
								window:perform_action(act.AdjustPaneSize({ dir, -diff }), pane)
							end
							break
						end
					end
				else
					local total = 0
					for _, p in ipairs(panes) do
						total = total + p.height
					end
					local target = math.floor(total / #panes)
					for _, p in ipairs(panes) do
						if p.is_active then
							local diff = target - p.height
							if diff > 0 then
								local dir = p.top == 0 and "Down" or "Up"
								window:perform_action(act.AdjustPaneSize({ dir, diff }), pane)
							elseif diff < 0 then
								local dir = p.top == 0 and "Up" or "Down"
								window:perform_action(act.AdjustPaneSize({ dir, -diff }), pane)
							end
							break
						end
					end
				end
			end),
		},

		-- フォントサイズ切替
		{ key = "+", mods = "CTRL", action = act.IncreaseFontSize },
		{ key = "-", mods = "CTRL", action = act.DecreaseFontSize },
		-- フォントサイズのリセット
		{ key = "0", mods = "CTRL", action = act.ResetFontSize },

		-- タブ切替 Cmd + 数字
		{ key = "1", mods = "SUPER", action = act.ActivateTab(0) },
		{ key = "2", mods = "SUPER", action = act.ActivateTab(1) },
		{ key = "3", mods = "SUPER", action = act.ActivateTab(2) },
		{ key = "4", mods = "SUPER", action = act.ActivateTab(3) },
		{ key = "5", mods = "SUPER", action = act.ActivateTab(4) },
		{ key = "6", mods = "SUPER", action = act.ActivateTab(5) },
		{ key = "7", mods = "SUPER", action = act.ActivateTab(6) },
		{ key = "8", mods = "SUPER", action = act.ActivateTab(7) },
		{ key = "9", mods = "SUPER", action = act.ActivateTab(-1) },

		-- コマンドパレット
		{ key = "p", mods = "SHIFT|CTRL", action = act.ActivateCommandPalette },
		-- 設定再読み込み
		{ key = "r", mods = "SHIFT|CTRL", action = act.ReloadConfiguration },
		-- キーテーブル用
		{ key = "s", mods = "LEADER", action = act.ActivateKeyTable({ name = "resize_pane", one_shot = false }) },
		{
			key = "a",
			mods = "LEADER",
			action = act.ActivateKeyTable({ name = "activate_pane", timeout_milliseconds = 1000 }),
		},
	},
	-- キーテーブル
	-- https://wezfurlong.org/wezterm/config/key-tables.html
	key_tables = {
		-- Paneサイズ調整 leader + s
		resize_pane = {
			{ key = "h", action = act.AdjustPaneSize({ "Left", 1 }) },
			{ key = "l", action = act.AdjustPaneSize({ "Right", 1 }) },
			{ key = "k", action = act.AdjustPaneSize({ "Up", 1 }) },
			{ key = "j", action = act.AdjustPaneSize({ "Down", 1 }) },

			-- Cancel the mode by pressing escape
			{ key = "Enter", action = "PopKeyTable" },
		},
		activate_pane = {
			{ key = "h", action = act.ActivatePaneDirection("Left") },
			{ key = "l", action = act.ActivatePaneDirection("Right") },
			{ key = "k", action = act.ActivatePaneDirection("Up") },
			{ key = "j", action = act.ActivatePaneDirection("Down") },
		},
		-- copyモード leader + [
		copy_mode = {
			-- 移動
			{ key = "h", mods = "NONE", action = act.CopyMode("MoveLeft") },
			{ key = "j", mods = "NONE", action = act.CopyMode("MoveDown") },
			{ key = "k", mods = "NONE", action = act.CopyMode("MoveUp") },
			{ key = "l", mods = "NONE", action = act.CopyMode("MoveRight") },
			-- 最初と最後に移動
			{ key = "^", mods = "NONE", action = act.CopyMode("MoveToStartOfLineContent") },
			{ key = "$", mods = "NONE", action = act.CopyMode("MoveToEndOfLineContent") },
			-- 左端に移動
			{ key = "0", mods = "NONE", action = act.CopyMode("MoveToStartOfLine") },
			{ key = "o", mods = "NONE", action = act.CopyMode("MoveToSelectionOtherEnd") },
			{ key = "O", mods = "NONE", action = act.CopyMode("MoveToSelectionOtherEndHoriz") },
			--
			{ key = ";", mods = "NONE", action = act.CopyMode("JumpAgain") },
			-- 単語ごと移動
			{ key = "w", mods = "NONE", action = act.CopyMode("MoveForwardWord") },
			{ key = "b", mods = "NONE", action = act.CopyMode("MoveBackwardWord") },
			{ key = "e", mods = "NONE", action = act.CopyMode("MoveForwardWordEnd") },
			-- ジャンプ機能 t f
			{ key = "t", mods = "NONE", action = act.CopyMode({ JumpForward = { prev_char = true } }) },
			{ key = "f", mods = "NONE", action = act.CopyMode({ JumpForward = { prev_char = false } }) },
			{ key = "T", mods = "NONE", action = act.CopyMode({ JumpBackward = { prev_char = true } }) },
			{ key = "F", mods = "NONE", action = act.CopyMode({ JumpBackward = { prev_char = false } }) },
			-- 一番下へ
			{ key = "G", mods = "NONE", action = act.CopyMode("MoveToScrollbackBottom") },
			-- 一番上へ
			{ key = "g", mods = "NONE", action = act.CopyMode("MoveToScrollbackTop") },
			-- viweport
			{ key = "H", mods = "NONE", action = act.CopyMode("MoveToViewportTop") },
			{ key = "L", mods = "NONE", action = act.CopyMode("MoveToViewportBottom") },
			{ key = "M", mods = "NONE", action = act.CopyMode("MoveToViewportMiddle") },
			-- スクロール
			{ key = "b", mods = "CTRL", action = act.CopyMode("PageUp") },
			{ key = "f", mods = "CTRL", action = act.CopyMode("PageDown") },
			{ key = "d", mods = "CTRL", action = act.CopyMode({ MoveByPage = 0.5 }) },
			{ key = "u", mods = "CTRL", action = act.CopyMode({ MoveByPage = -0.5 }) },
			-- 範囲選択モード
			{ key = "v", mods = "NONE", action = act.CopyMode({ SetSelectionMode = "Cell" }) },
			{ key = "v", mods = "CTRL", action = act.CopyMode({ SetSelectionMode = "Block" }) },
			{ key = "V", mods = "NONE", action = act.CopyMode({ SetSelectionMode = "Line" }) },
			-- コピー
			{ key = "y", mods = "NONE", action = act.CopyTo("Clipboard") },

			-- コピーモードを終了
			{
				key = "Enter",
				mods = "NONE",
				action = act.Multiple({ { CopyTo = "ClipboardAndPrimarySelection" }, { CopyMode = "Close" } }),
			},
			{ key = "Escape", mods = "NONE", action = act.CopyMode("Close") },
			{ key = "c", mods = "CTRL", action = act.CopyMode("Close") },
			{ key = "q", mods = "NONE", action = act.CopyMode("Close") },
		},
	},
}
