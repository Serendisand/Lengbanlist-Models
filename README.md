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

详见 [Lengbanlist docs/CustomModel 格式](https://github.com/Serendisand/Lengbanlist)。

最小示例:

```yaml
name: "YourModelName"        # 切换时用的标识

help:
  - "§b帮助菜单第 1 行"
  - "§b帮助菜单第 2 行"

messages:
  add-ban: "§c{player} 已被封禁 {days}!"
  remove-ban: "§a{player} 已解封"
  # ... 更多键 (详见 Lengbanlist CustomModel.java)
```

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
- 单模型不超过 8 KB

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
