# atlas-plugins

Atlas 自建插件市场（marketplace）仓库。AtlasHarness 启动时会自动预装本市场
（registry key = manifest 名 `atlas-plugins`，与 `agent-skills` / `openai-codex`
预装同一机制；可用 `ATLAS_DISABLE_ATLAS_MARKETPLACE_AUTOINSTALL=1` 关闭）。

> 分工约定：**官方第三方 skill 走官方仓**（Ascend `agent-skills` / OpenAI
> `openai-codex`，只读不修改）；**自建 skill 走本仓库**。

## 目录结构

```
atlas-plugin/marketplace.json      # 市场清单（name 即 registry key，勿改）
plugins/example-plugin/            # 示例插件（scaffold 生成，可删可改）
  atlas-plugin/plugin.json         #   插件清单
  commands/example.md              #   示例命令
  skills/example-skill/SKILL.md    #   示例技能
```

## 新增插件 / 技能

1. 复制 `plugins/example-plugin/` 为新目录（如 `plugins/my-skill-pack/`），
   改 `atlas-plugin/plugin.json` 的 `name`，放你的 `commands/` 与 `skills/`。
2. 在 `atlas-plugin/marketplace.json` 的 `plugins` 数组里登记
   （`source` 用字符串相对路径，如 `./plugins/my-skill-pack`）。
3. 提交并推送；客户下次启动 AtlasHarness 即自动拉到更新（git 源不 pin，
   自然收敛）。

本地调试（在 AtlasHarness 仓库内）：

```bash
bun run src/launcher.ts plugin marketplace add /path/to/atlas-plugins-marketplace
bun run src/launcher.ts plugin marketplace publish --plugin ./plugins/my-skill-pack --marketplace /path/to/atlas-plugins-marketplace
```

## 仓库约定

- 分支 `master`；提交信息中文 + scope 前缀（如 `feat(my-skill): 新增 xx 技能`）。
- 本仓库为**公开**仓库（客户匿名克隆预装，私有仓库会导致预装失败）。
- 技能内容遵循 AtlasHarness 的 skill 契约（goal + gates，工具返回证据而非决策）。
