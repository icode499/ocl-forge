# Golden Examples 选取指南

## 目的

从现有 100 个样例中精选 5 个，覆盖最常见的 OCL inv 模式，作为 prompt 的固定 few-shot 样例。

## 五个类别

| # | 文件 | OCL inv 模式 | 典型操作 | 选取标准 |
|---|------|-------------|----------|----------|
| 1 | golden-01-attribute.md | 简单属性约束 | `self.<attr> <op> <value>` | 单属性比较、范围检查 |
| 2 | golden-02-collection.md | 集合量词约束 | `forAll` / `exists` / `select` | 对关联集合做量词判断 |
| 3 | golden-03-navigation.md | 关联导航约束 | `self.<assoc>.<attr>` | 跨对象引用、多级导航 |
| 4 | golden-04-enum-condition.md | 枚举状态条件约束 | `implies` / `if-then-else` | 基于枚举值的条件分支 |
| 5 | golden-05-compound.md | 复合聚合约束 | `collect` / `sum` / `let` | 聚合计算、let 绑定 |

> 注意：v1 不支持 pre/post，因此没有前置/后置条件的 golden example。

## 选取标准

1. **代表性**：该类别中最典型的 inv 用法
2. **复杂度适中**：不要太简单（没有学习价值），不要太复杂（占用过多 token）
3. **业务语义清晰**：业务描述和 OCL 之间的对应关系一目了然
4. **测试完整**：有正例和反例，含比较运算符的规则有边界例

## 每个样例必须包含

整体遵循 `prompt/fragments/07-output-format.md` 的四阶段结构（`<stage1>` 到 `<stage4>`）。
固定区样例允许使用 compact 变体，例外仅限：
- stage4 可使用 `## 审查结论` + 一行结论，不展开完整审查表格（节省 token）
- 其余 stage1/stage2/stage3 的结构标签与顺序保持不变

## 操作步骤

1. 对 100 个样例的 OCL 代码按上述 5 个模式做分类
2. 每类按选取标准排序，选出最佳的 1 个
3. 为选出的样例补充完整四阶段输出
4. 填入对应的 `golden-*.md` 文件
5. 更新 `VERSION` 文件中的 golden 版本号

## Token 预算

- 每个 golden example 目标控制在 ~500 token 以内
- 5 个总计 ~2500 token
- 阶段 4 精简为一行结论可显著减少 token
