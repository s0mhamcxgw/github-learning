# 本机接入与素材处理

课程仓库：`E:\Documents\ChatGPT\obsidian\视频课程`。读书仓库“我的笔记”不作为本Skill的默认目标。项目输出在 `E:\Documents\ChatGPT\obsidian\outputs`，课程抓取、音频、模型和转写缓存放在项目 `work`。

## 当前课程定位

Windows命令：`& '<本Skill目录>\scripts\get_edge_course.ps1'`。它只读取唯一匹配课程窗口的地址栏，并去掉视频链接的追踪参数；多个匹配窗口时应缩小TitlePattern或请用户提供链接，不猜测其他标签。

## B站素材

`fetch_bilibili.py --url '<url>' --work-dir '<绝对工作目录>'` 获取视频名、发布者、分P、CID、时长与当前课字幕。加 `--download-audio` 时，只有当前课未返回字幕才尝试公开播放器正常返回的音轨。脚本不读取浏览器Cookie，不处理登录、付费或限制绕过，也不写仓库笔记。接口可能变化，遇到明确失败不反复请求同一个受限资源。

原始课程ID与分P/CID用于增量更新。`course.json` 是目录数据，`part-NNN-manifest.json` 说明素材获得情况；无字幕时不得把目录数据当成课程实际授课内容。

## 本机转写

2026-11-05在项目 `work\course-study-20261105\asr-deps` 安装了独立的faster-whisper依赖；本机Python为 `E:\python\python.exe`。先检查依赖和模型是否仍存在，再复用；不要假定换台设备也有同一路径。

模型和缓存放E盘。使用faster-whisper时设置本机模型路径、`device="cpu"`、`compute_type="int8"`、适当的CPU线程数，并实际迭代segments生成器才会完成转写。中文课程显式设定中文语言，保留每段起止秒数；术语提示只辅助拼写，不能拿提示词代替实际识别结果。参考[项目使用说明](https://github.com/SYSTRAN/faster-whisper)。

用Skill内 `scripts/transcribe_local.py` 转写音轨；参数为 `--audio '<音轨>' --output-json '<工作目录/转写缓存.json>' --model-cache '<E盘模型目录>' --deps-dir '<现有依赖目录>' --source-url '<分P来源链接>'`。本机模型可复用 `E:\Documents\ChatGPT\obsidian\work\course-study-20261105\models`。

本机faster-whisper 1.2.1搭配PyAV 19时，文件名解码会因`metadata_errors`参数被移除而失败。该脚本已用PyAV先解码为16kHz单声道float32数组，再把数组传给transcribe；不修改用户全局依赖或第三方包源码。`--max-seconds`只用于明确要求的片段或短验证，不能把片段结果当整节完成。缓存按音轨哈希及参数匹配，不覆盖不同来源的同名转写。

只对用户指定的课时做音频处理。自动转写的原始片段是工作素材；交付课程笔记时用自己的话归纳，附视频时间点，标明识别误差，避免把完整字幕堆进笔记。

## 写入和应用内核对

先列出目标目录并读取适用规则。新“视频课程”库初始只有“欢迎.md”，可以按课程建立文件夹。保留欢迎文件、已有笔记、用户标记和学习状态；后续沿用已建立结构。

Obsidian CLI是 `D:\01_应用软件\02办公阅读\Obsidian\Obsidian.com`。本项目旧包装脚本固定“我的笔记”，不要借它把课程写错仓库；直接指定 `vault=视频课程`。先用help确认所需命令。

需要eval时，把较长JS保存到E盘work，再用短参数 `code=eval(require('fs').readFileSync('E:/.../check.js','utf8'))` 加载；Windows直接传长JS曾导致参数序列化错误。核对新文件被识别、目录和时间链接目标正确，打开当前课或课程目录。

不要把创建课程笔记解释为自动授权修改Obsidian插件、认证、模型、全局设置或后台监听；本流程通过用户调用执行。
