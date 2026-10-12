# 超星内置浏览器操作细节

这些控件曾在超星学习页验证，使用前以当前工具文档和页面为准。不要导入旧会话的标签页 ID、认证 URL 或坐标。

## 播放与等待

播放器常在 `#iframe → iframe`，题区再进入 `#frame_content`：

```javascript
var media = course.playwright.frameLocator('#iframe').frameLocator('iframe');
var quiz = media.frameLocator('#frame_content');
var timing = await media.locator('video').evaluate(v => ({
  capturedAt: Date.now(), currentTime: v.currentTime,
  duration: v.duration, playbackRate: v.playbackRate, paused: v.paused
}));
```

正常播放按钮曾为“播放视频”，恢复按钮为“播放”；精确匹配避免命中“播放速度”。保持页面正常速度。

`duration` 为 null、非有限数或≤0时不生成截止时间，待元数据加载补读一次。截止时间变量在 REPL 顶层保存。恢复时读取新的时间戳与剩余时长，不重新等待整段视频。

等待每段毫秒取整数，≤55000。此环境曾有约300秒传输上限；纯等待批次可约220秒，等待后还要执行 UI 时预留额外时间。某些工具步骤曾耗时约21秒，批次超时不意味着动作没有完成。仅等待无需页面扫描，可输出本地剩余秒数。

## 批量答题

- 单选/判断：`li.before-after`；多选：`li.before-after-checkbox`。先按本页题型及选项建立映射，再用定位器操作，不沿用历史序号。
- 一次核对：读取 `li[aria-checked="true"]`。字体异常时 DOM 文本只用于选中标记，题意以截图为准。
- 长题页下方的定位点击曾失败。分当前可见区域填写；需要到页底时可用 `courseIab.pressKey(null, 'ctrl+End')`，回顶部用 `ctrl+Home`。
- `locator('body').evaluate(...)` 等读取也曾自动滚动页面。因此先完成全部核对，再到提交位置截图，然后直接按截图点击文字。定位器失败或读取后，不复用旧截图坐标。
- `fullPage` 截图用于读题，其坐标不能直接当作当前视口坐标。视口、滚动、题数、目录状态或弹窗改变时重新定位。

## 提交与恢复

提交控件曾为 `a.btnSubmit`；确认在顶层 `#popok`。提交定位失败时查看当前状态，按钮确实可见再用当前视口坐标；确认按钮不可见时不要继续点击。

```javascript
var result = await quiz.locator('body').evaluate(e => ({
  score: e.innerText.match(/本次成绩\s*([\d.]+)分/)?.[1],
  complete: /已完成/.test(e.innerText)
}));
```

“下一节”可用顶层精确角色定位。真实完成后再进入下一节。

用户打开新的学习页后，若标签包装对象失效，应重新绑定当前标签页；不要换浏览器、重复加载学习页或重做全部题目。超时恢复先读取已选状态，避免重复点击把已选多选项取消。
