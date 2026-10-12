# 自动刷课

中文 Codex skill：在用户授权的超星/学习通课程中，通过正常浏览器界面续学视频、处理章节练习，并减少重复截图、全局扫描和逐题确认。

适用场景：已登录课程的续学、需要鼠标停留播放器的课程、短章节练习，以及希望按章节衡量 token 消耗的工作流。它是给 Codex 的操作指导，不是独立运行的刷课软件。不会修改学习记录、跳过播放、绕过验证码或自动扩展到考试。

## 环境

- 支持浏览器控制工具的 Codex；本工作流在桌面版内置浏览器验证。
- 用户自行登录，并打开课程页面；浏览器工具需允许正常点击、截图及页面状态读取。
- 可选 Python 3.10+：用于本地 token 统计，只有标准库依赖。

## 安装

克隆本仓库后，把 `skills/chaoxing-course-workflow` 文件夹放到你的 Codex skills 目录。Windows PowerShell：

```powershell
git clone https://github.com/YAOsy040101/auto-course.git
$skillRoot = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills' } else { Join-Path $env:USERPROFILE '.codex/skills' }
$skillTarget = Join-Path $skillRoot 'chaoxing-course-workflow'
if (Test-Path -LiteralPath $skillTarget) { throw '已安装：请先备份现有技能再更新。' }
New-Item -ItemType Directory -Force -Path $skillRoot | Out-Null
Copy-Item -LiteralPath './auto-course/skills/chaoxing-course-workflow' -Destination $skillTarget -Recurse
```

macOS/Linux 同样复制整个技能文件夹到 `${CODEX_HOME:-$HOME/.codex}/skills/`。在新一轮对话中使用；未显示时重启 Codex。

## 使用

打开已登录的课程，然后发送：

> 使用 $chaoxing-course-workflow，从当前未完成章节继续。正常观看视频，鼠标停在播放器；结束后完成章节练习并提交，再进入下一节。视频期间不扫描进度。记录每节 token 使用量。

也可指定仅播放视频、仅辅导练习或限定章节范围。技能不会自行获得提交权限，按你在对话中的授权执行。不同课程改版后需重新确认控件；代码示例中的 `course`、`courseIab` 必须先通过当前浏览器工具绑定，不能直接在普通 Node.js 或网页控制台运行。

## 优化机制

1. 一次读取播放状态，以绝对截止时间扣除已过去的时间。
2. 播放期间只等待；暂停后按剩余时长恢复。
3. 集中读题和查证，批量选择，最后核对一次。
4. 长页面读取可能自动滚动：核对完成后重新定位提交，避免旧坐标误点。
5. 超时后保留已执行结果，只补缺失动作。

不携带固定坐标或答案题库。布局与答案缓存仅属于使用者当前任务，必须验证后复用。

## Token 统计

```powershell
python skills/chaoxing-course-workflow/scripts/chapter_usage.py CURRENT_THREAD.jsonl 2.2 2026-01-01T10:00:00Z 2026-01-01T10:15:00Z chapter-usage.csv
```

显式指定当前任务的日志，不批量搜索其他会话。统计相邻累计计数的差值，按日志事件粒度归属，不能代表精确计费。输出包括输入、缓存输入、未缓存输入、输出、总量及工具调用数；重复章节覆盖该行。缺失计数或计数器重置时失败并保留 CSV。

50% 消耗下降是需要实测的目标，不作保证。比较时需控制题数、视频长度、上下文规模和统计口径；缓存输入不能在总输入上重复相加。

## 开发与验证

```powershell
python -m unittest discover -s tests -v
```

`SKILL.md` 是入口；`references/browser-details.md` 按需加载。提交问题时请去除课程认证参数、个人信息、会话日志和成绩截图。

MIT License。非超星官方项目。
