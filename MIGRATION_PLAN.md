# 迁移与改造计划

## 概况

将 `~/hexo/source/_posts/`（187 篇）迁移至 astro-whono 主题，按内容类型拆分为四个 collection，
并新增层级分类浏览功能。

## 内容分配

| 原 hexo categories 顶级 | Astro collection | URL 前缀 | 篇数 |
|---|---|---|---|
| `fanfiction` | `essay` | `/essay/` | 136 |
| `fiction` | `fiction` | `/fiction/` | 18 |
| `Non-fiction` | `nonfiction` | `/nonfiction/` | 2（未来可扩展）|
| 其他（Photo/Video/Archive/learning/Critic/杂谈/碎片随笔） | `bits` | `/bits/` | 31 |

## Sidebar 导航

```
同人作品 / Fan Fiction    /essay/
原创作品 / Fiction         /fiction/
非虚构 / Non-Fiction       /nonfiction/
其他 / Misc               /bits/
分类                       /category/
归档                       /archive/
关于                       /about/
```

---

## 完成状态

### ✅ 已完成

- [x] **Schema 扩展**（`src/content.config.ts`）
  - 新增 `fiction`、`nonfiction` collection，schema 与 essay 相同
  - 所有 article collection（essay/fiction/nonfiction）加入 `categories`、`updated` 字段
  - `bits` collection 同样加入 `categories`、`updated` 字段

- [x] **迁移脚本**（`migrate.py`）
  - 按顶级 category 分流到四个目录
  - 修复两处 frontmatter 错误：post 167（`ategories` typo）、post 194（`copiright` typo）
  - hexo `permalink` 转为 kebab-case `slug`（`_` → `-`）
  - 原样保留 HTML 内容和 `<!-- more -->` 标记
  - 输出文件名：数字前缀 + `.md`（如 `001.md`）

- [x] **迁移执行**（`python3 migrate.py`）
  - essay: 136 篇（essay 实际产出 137，含一个归类边界）
  - fiction: 18 篇
  - nonfiction: 2 篇
  - bits: 30 篇
  - errors: 0

- [x] **图片处理**
  - 将 `~/hexo/source/images/` 的 20 张图片复制到 `public/images/`
  - 修复 069.md、151.md 中的相对路径 `images/xxx` → `/images/xxx`

- [x] **Fiction 路由**（新建 3 个文件）
  - `src/pages/fiction/index.astro`
  - `src/pages/fiction/page/[page].astro`
  - `src/pages/fiction/[...slug].astro`

- [x] **Non-Fiction 路由**（新建 3 个文件）
  - `src/pages/nonfiction/index.astro`
  - `src/pages/nonfiction/page/[page].astro`
  - `src/pages/nonfiction/[...slug].astro`

- [x] **分类浏览页**（新建 2 个文件）
  - `src/pages/category/index.astro`（`/category/`）：分类树，按顶级分类分组，显示子分类
  - `src/pages/category/[...slug].astro`（`/category/fanfiction/` 等）：前缀匹配，显示面包屑 + 子分类入口 + 按年分组的文章列表

- [x] **侧边栏导航**（`src/components/Sidebar.astro`）
  - 更新所有标签，新增 Fiction/Non-Fiction/分类入口

- [x] **文章页面包屑**（`src/layouts/ArticleLayout.astro`）
  - 在发布日期/标签行下方加分类面包屑
  - categories 为空时不渲染

- [x] **页面标题更新**
  - `src/pages/essay/index.astro` + `page/[page].astro`：随笔 → 同人作品 / Fan Fiction
  - `src/pages/bits/index.astro`：絮语 → 其他 / Misc

- [x] **构建验证**：`npm run build` 成功，373 个页面，0 错误

---

## 关键文件索引

| 文件 | 说明 |
|------|------|
| `migrate.py` | 迁移脚本，可重复运行（会覆盖已有输出）|
| `src/content.config.ts` | Schema 定义，所有 collection |
| `src/content/essay/` | 同人作品（136 篇）|
| `src/content/fiction/` | 原创作品（18 篇）|
| `src/content/nonfiction/` | 非虚构（2 篇）|
| `src/content/bits/` | 其他/Misc（31 篇 + 主题示例）|
| `src/pages/category/` | 分类浏览路由 |
| `src/pages/fiction/` | 原创作品路由 |
| `src/pages/nonfiction/` | 非虚构路由 |
| `public/images/` | 本地图片资源（从 hexo 迁移）|

---

## 待办 / 可选后续

- [ ] 删除 `src/content/bits/` 中的主题示例文章（late-night-cafe.md 等）
- [ ] 更新 `site.config.mjs` 中的站点标题、作者信息、SITE_URL
- [ ] 自定义 `/about/` 页面内容
- [ ] 为 fiction/nonfiction 添加 RSS 支持（参照 essay RSS 实现）
- [ ] 为 `/category/` 分类页添加分页（目前 fanfiction 层级显示全部 136 篇）
