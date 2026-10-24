# 📊 月度精选数据源：bStats REST API

用于**自动评选每月精选**：插件通过 bStats 自定义图表上报当前使用的模型，
模型仓库的轮换工作流每月 1 号调用 bStats 官方 REST API，选出被最多服务器使用的模型。

> 以前的 Cloudflare Worker 聚合端点已不再参与评选，相关代码已删除。
> 官方文档：<https://bstats.org/docs/rest-api>

## 架构

```
各服插件 (bStats 自动上报)                 GitHub 仓库
   SimplePie "modelUsage"                    │ GitHub Action (每月 1 号)
        │ 当前模型（每服 1 票）               ▼
        └────────► bStats 插件页 ◄──── GET /api/v1/plugins/33262/charts/modelUsage/data
                       33262                              │
                                                          ▼
                                              rotate_featured.py → index.json
```

## 一、bStats 侧（一次性）

插件页已经存在，**不需要新建**：
<https://bstats.org/plugin/bukkit/Lengbanlist/33262>（ID `33262`，与插件代码里的
`new Metrics(this, 33262)` 一致）。

只需要给这个页面加一张自定义图表：

1. 登录 bStats，打开插件页 → **Edit**
2. 添加图表（Add chart）
   - 类型：**Simple Pie**
   - Chart ID：`modelUsage` ← 必须一字不差
   - 标题随你喜欢，例如 `Model`
3. 保存

> bStats 要求网页上注册的 chart ID 与代码里提交的完全一致，否则数据会被丢弃。
> 注册后要等装了新版本插件的服务器上报一次（启动后约 3 分钟首次提交，之后每 30 分钟），
> 图表才会开始有数据。

## 二、插件侧（已接好）

`Lengbanlist.java` 在创建 Metrics 后注册图表：

```java
metrics = new Metrics(this, 33262);
metrics.addCustomChart(new Metrics.SimplePie("modelUsage", () -> {
    String model = ModelManager.getCurrentModelName();
    return model == null || model.isEmpty() ? "unknown" : model.toLowerCase(Locale.ROOT);
}));
```

- 上报值是**当前模型的 id**（小写），与 `index.json` 里的 `id` 对齐
- 内置 `Default` / `English` 也会上报，但评选时会被过滤掉
- 玩家切换模型后，下一轮上报自动更新（无需重启）
- 服主可以在 `plugins/bStats/config.yml` 里整体关闭 bStats

## 三、仓库侧（GitHub Actions）

`.github/rotate_featured.py` 直接请求：

```
GET https://bstats.org/api/v1/plugins/33262/charts/modelUsage/data
→ [{"name":"hutao","y":3},{"name":"furina","y":1}]
```

- **不需要任何 secret**
- 默认值已写死在脚本里；要改的话在
  Settings → Secrets and variables → Actions → **Variables** 添加：

  | Variable | 默认值 | 说明 |
  | --- | --- | --- |
  | `BSTATS_PLUGIN_ID` | `33262` | bStats 插件页 ID |
  | `BSTATS_CHART_ID` | `modelUsage` | 自定义图表 ID |

- 图表无数据 / 接口异常 / 返回了未知模型时，自动回退到顺序轮换，Action 不会失败

## 四、验证

```bash
# 图表是否注册成功（返回的 JSON 里应能看到 modelUsage）
curl -s https://bstats.org/api/v1/plugins/33262/charts | grep -o '"modelUsage"'

# 当前分布（新图表一开始是 []，有服务器上报后才有内容）
curl -s https://bstats.org/api/v1/plugins/33262/charts/modelUsage/data
```

也可以直接看网页：<https://bstats.org/plugin/bukkit/Lengbanlist/33262>

## 五、统计口径

- **每台服务器 1 票**：上报的是"当前正在使用的模型"，不是累计安装次数
- 饼图只保留当前快照，bStats 没有按月历史；每月 1 号读取 = 上月末的分布
- 并列时按模型 id 字典序取第一个，保证每次结果稳定
- 只从 `index.json` 里已上架的模型中选择；`default` / `english` / 玩家自定义模型会被忽略

## 六、旧方案（已移除）

`worker/` 是之前的 Cloudflare Worker 聚合端点，已随迁移删除；工作流不再读取
`STATS_API_URL`，插件侧的 `models-cloud.stats` 配置和自定义上报代码也已经移除。
Cloudflare 上的 Worker 和 KV 可以自行删除。
