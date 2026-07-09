local wezterm = require("wezterm")
local config = wezterm.config_builder()

config.keys = require("keybind").keys
config.key_tables = require("keybind").key_tables
config.disable_default_key_bindings = true
config.leader = {
	key = "F1",
	timeout_milliseconds = 2000,
}
config.automatically_reload_config = true
config.font_size = 20.0
config.font = wezterm.font_with_fallback({
	"JetBrains Mono",
	"Hiragino Sans",
	"Apple Color Emoji",
})
config.use_ime = true
config.window_background_opacity = 1.0
config.macos_window_background_blur = 10
config.background = {
	{
		source = { Color = "rgba(0, 0, 0, 0.5)" },
		height = "100%",
		width = "100%",
	},
}

-- 背景画像のファイル名
-- local background_path = wezterm.config_dir .. "/night.png"

config.native_macos_fullscreen_mode = true
config.window_decorations = "RESIZE"
config.window_frame = {
	inactive_titlebar_bg = "none",
	active_titlebar_bg = "none",
}

-- 背景画像設定
-- config.background = {
-- 	{
-- 		source = { File = background_path },
-- 		opacity = 0.95,
-- 		hsb = {
-- 			brightness = 3.0,
-- 			hue = 1.0,
-- 			saturation = 0.8,
-- 		},
-- 	},
-- 	{
-- 		source = { Color = "rgba(0, 0, 0, 0.7)" },
-- 		height = "100%",
-- 		width = "100%",
-- 	},
-- }

-- config.window_background_gradient = {
-- 	colors = { "#000000" },
-- }

config.show_new_tab_button_in_tab_bar = false

config.colors = {
	foreground = "#FFFFFF",
	cursor_bg = "#FFFFFF",
	cursor_fg = "#000000",
	ansi = {
		"#4B4B4B", -- black (少し明るめに)
		"#FF6B6B", -- red
		"#69FF94", -- green
		"#FFFF6B", -- yellow
		"#6BB5FF", -- blue
		"#FF6BFF", -- magenta
		"#6BFFFF", -- cyan
		"#FFFFFF", -- white
	},
	brights = {
		"#7A7A7A", -- bright black
		"#FF8A8A", -- bright red
		"#8AFFB0", -- bright green
		"#FFFF8A", -- bright yellow
		"#8AC8FF", -- bright blue
		"#FF8AFF", -- bright magenta
		"#8AFFFF", -- bright cyan
		"#FFFFFF", -- bright white
	},
	tab_bar = {
		inactive_tab_edge = "none",
	},
}

local SOLID_LEFT_ARROW = wezterm.nerdfonts.ple_lower_right_triangle
local SOLID_RIGHT_ARROW = wezterm.nerdfonts.ple_upper_left_triangle

wezterm.on("format-tab-title", function(tab, tabs, panes, config, hover, max_width)
	local background = "#5c6d74"
	local foreground = "#FFFFFF"
	local edge_background = "none"

	if tab.is_active then
		background = "#b62560"
		foreground = "#FFFFFF"
	end

	local edge_foreground = background
	local title = " " .. wezterm.truncate_right(tab.active_pane.title, max_width - 1) .. " "

	return {
		{ Background = { Color = edge_background } },
		{ Foreground = { Color = edge_foreground } },
		{ Text = SOLID_LEFT_ARROW },
		{ Background = { Color = background } },
		{ Foreground = { Color = foreground } },
		{ Text = title },
		{ Background = { Color = edge_background } },
		{ Foreground = { Color = edge_foreground } },
		{ Text = SOLID_RIGHT_ARROW },
	}
end)

return config
