# Lengbanlist-Models

> Lengbanlist 插件的角色风格模型仓库 —— 云端拉取,每月更新

## 版权声明 / Disclaimer

**本仓库所有角色风格仅用于游戏插件消息风格化,角色版权归原版权方所有。**

- 角色版权归 [Cognosphere Pte. Ltd.](https://www.hoyoverse.com/) / miHoYo 等原版权方所有
- 本项目与上述版权方**无任何隶属、赞助或官方合作关系**
- 所有角色形象、台词、设定均来自原版权方公开发布的内容,使用已构成合理使用 (fair use)
- 这些**只是消息风格** (`"胡桃风格"` 而非冒充胡桃本人)
- 如版权方有任何异议,请通过 [issue](https://github.com/Serendisand/Lengbanlist-Models/issues) 联系,**会立即下架相关模型**

These models are fan-made styling only — **NOT affiliated with miHoYo / HoYoverse / Cognosphere**.

---

## 📊 月度精选自动评选

搭建统计聚合端点即可让每月精选 = 上月被最多服务器采纳的模型（免费方案 + 完整代码）:
[部署教程](docs/aggregation-endpoint.md)

---

## 用法 (服务器管理员)

Lengbanlist 插件内置 `/lban models` 命令集:

```bash
/lban models refresh                  # 从云端拉取最新索引
/lban models list                     # 列出本地 + 云端模型
/lban models install <model-id>       # 下载并安装指定模型到本地
/lban models pin <model-id>           # 锁定本地模型,云端更新不再覆盖
/lban models unpin <model-id>         # 解除锁定
```

模型 ID 在 `/lban models list` 中查看 (例如 `hutao` / `furina` / `keqing`)。

切换模型:
```bash
/lban model HuTao                      # 切换到胡桃风格 (内置)
/lban model hutao                      # 切换到云端安装的胡桃风格 (若已 install)
```

---

## 目录结构约定

```
/
├── index.json                  ← 模型清单 + 版本 + 月度精选
├── README.md                   ← 本文件
├── LICENSE                     ← 仓库许可证
└── models/
    └── <model-id>/             ← 单个模型,目录名 = model id
        ├── <model-id>.yml      ← 模型内容 (Lengbanlist CustomModel 格式)
        └── meta.json           ← 可选元数据 (version / author / tags)
```

`<model-id>` 使用小写,**不含连字符** (例如 `hutao` 而非 `hu-tao`),与 Lengbanlist 内置 Java 模型命名风格一致。

---

## YAML 模型格式

模型文本**支持继承**：插件内置一份全局默认 (`models/_base.yml`)，模型文件只写自己不一样的部分，
没写的字段自动沿用全局默认。**插件新增命令/文案时，本仓库的模型不需要跟着改。**

最小示例 (只覆写想要的字段):

```yaml
name: "YourModelName"        # 切换时用的标识 (必填)
version: "1.0.0"             # 版本号,index.json 由 CI 自动同步

help-overrides:              # 可选:只改帮助菜单里想改的那几行
  "#title": "§b║ §2§oLengbanlist 帮助 - 你的风格 §b║"   # 帮助框标题行
  "#version": "§2♡ 当前版本: {version} §7| §b模型: 你的模型"
  "lban freeze": "> 把人定住～"                          # 只换描述文字(最短写法)
  "lban add": "§e✦ §b/lban add ... §7- §3整行替换,想改符号颜色时用"

messages:                    # 只写要改的键
  add-ban: "§c{player} 已被封禁 {days}!"
  remove-ban: "§a{player} 已解封"
  # ... 更多键见 plugins/Lengbanlist/models/_base.yml

console:                     # 可选:插件在服务端控制台说的话(启动/关闭横幅),也能带上人设
  ready: "§bLengbanlist §6堂主到岗![]~(￣▽￣)~* §7v{version} §7| §3模型 {model} §7| §3服务端 {server}"
  loading: "§f原神§2正在加载,堂主马上就来～"
  tip: "§6堂主偷偷告诉你: §e{tip}"
  placeholder-hook: "§aPlaceholderAPI 接上啦,%lengbanlist_*% 都能用～"
  auto-update: "§a自动更新开着呢,堂主正在看看有没有新版～"
  shutdown: "§k§4打烊啦,堂主正在收拾行李qwq..."
  farewell: "§f往生堂今日打烊,下次再来哦～"
```

`messages` 段常用占位符（插件负责把内容填好,模型只管摆位置）:

| 占位符 | 内容 |
|------|------|
| `{player}` / `{target}` | 玩家名 |
| `{ip}` | IP 地址 |
| `{reason}` | 处罚原因 |
| `{days}` / `{duration}` | **已经格式化好的时长**:`30秒` / `5分钟` / `3小时` / `3天` / `1周` / `1个月` / `永久`(英文模型为 `30 seconds` / `1 day` / `permanently`)。**它自带单位,后面不要再写"天"** |
| `{remaining}` | 剩余时长,格式同上(已到期为 `已到期`,英文 `expired`) |
| `{type}` | 处罚类型:中文模型为 `封禁` / `禁言`,英文模型为 `ban` / `mute` |
| `{count}` | 次数 / 条数 |
| `{version}` | 插件版本号 |

完整占位符表见插件内置 `plugins/Lengbanlist/models/_base.yml` 顶部注释。

`console` 段共有 7 个键，只写想改的即可，其余沿用 `models/_base.yml`（中文默认）：

| 键 | 出现时机 | 占位符 |
|------|------|------|
| `ready` | 插件启用完成 | `{version}` 插件版本、`{model}` 模型名、`{server}` 服务端版本 |
| `loading` | 开始启用时 | — |
| `tip` | 启动后随机一句一言（前面会自动加上模型名） | `{tip}` |
| `placeholder-hook` | 检测到 PlaceholderAPI 时 | — |
| `auto-update` | 自动更新功能开启时 | — |
| `shutdown` | 插件停用开始 | — |
| `farewell` | 插件停用结束 | — |

> 诊断类日志（数据库报错、跨服同步失败、webhook 重试等）不参与模型化，固定中文，便于排障。

`help-overrides` 的键有两种写法：

键（两种）：

| 写法 | 作用 |
|------|------|
| `"lban add"` / `"lban freeze"` / `"ban-ip"` / `"setban"` | 覆写该命令所在的那一行（按命令名匹配，取第一条命中的行） |
| `"#top"` / `"#title"` / `"#split"` / `"#bottom"` / `"#version"` | 覆写帮助框的边框行、标题行、页脚行 |

值（两种）：

| 写法 | 作用 |
|------|------|
| `"> 描述文字"` | **只替换描述部分**，命令用法沿用全局默认 —— 推荐，最短 |
| `"§e✦ §b/lban freeze ... §7- §3描述"` | 整行替换（想改前面的符号/颜色时才需要） |

符号与颜色不同（比如可莉用 `§e✦`）的模型，在文件顶部声明一次即可，命令行依然可以用最短写法：

```yaml
help-bullet: "§e✦"          # 不写则用全局默认 §2✦
help-overrides:
  "lban freeze": "> 把坏孩子冻住，让他动不了！"
```

> 想整份帮助都自己写也可以：直接给 `help:` 一个完整列表（老写法仍然支持）。
> 只是想微调几行的话，用 `help-overrides` 更省事，插件加新命令时你不用动。

---

## 月度精选 (Featured)

`index.json` 的 `featured.month` 字段 (格式 `yyyy-MM`) 用于插件 GUI 顶部 banner 推荐本月模型。每月 1 号可手动更新为新的精选。

---

## 贡献流程 (添加/修改模型)

1. Fork 本仓库
2. 在 `models/<your-id>/<your-id>.yml` 创建或修改模型文件
3. 更新 `index.json` 中对应条目 (`version` 字段递增)
4. 提交 PR —— 标题写明 "Add: 模型名" 或 "Update: 模型名 版本号"
5. 等待 review 后合并

**审核标准**:
- 角色风格一致,无敏感/争议内容
- 颜色代码 + 占位符语法正确
- 只覆写必要字段 (`messages` 里不必重复全局默认的原话,`help-overrides` 只写要改的行)
- 单模型不超过 12 KB

---

## 镜像

插件默认按以下顺序尝试镜像 (首个成功即用):

1. `https://raw.githubusercontent.com/Serendisand/Lengbanlist-Models/main/index.json`
2. `https://gh-proxy.com/...` (国内加速)
3. `https://mirror.ghproxy.com/...` (国内备用)

可在插件 `config.yml` 中配置自定义镜像:

```yaml
models-cloud:
  enabled: true
  repo: Serendisand/Lengbanlist-Models
  branch: main
  mirrors: []  # 留空使用默认镜像链
```

---

## License

本仓库代码与配置: [Attribution-NonCommercial-ShareAlike 4.0 International](LICENSE)

模型内容 (YAML): 仅供游戏插件消息风格化使用,角色版权归原版权方所有。
