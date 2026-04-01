## 输出格式

严格按以下阶段标签分隔四个阶段的输出。不要在标签外输出任何内容。

这些标签是结构化分段定界符，不要求整体内容可被 XML 解析；阶段内容中可出现 OCL/C++ 的 `<`、`<=` 等符号。

以下示例为结构示意。`<stage3>` 内允许在块开头一次性出现文件级 harness 样板（如 `#include`），不要求为每条规则重复。

```text
<stage1>
## 模型结构
[表格...]

## 关联关系
[表格...]

## 枚举类型
[表格或「无」]

## 业务约束规则
[表格...]

## 信息缺口
[表格或「无信息缺口」]
</stage1>

<stage2>
-- R1: [规则描述]
context [Class]
inv [constraintName]:
  [OCL 表达式]

-- R2: [规则描述]
...
</stage2>

<stage3>
// R1: [规则描述]
TEST([Class]Test, [constraintName]_positive) {
    ...
}
TEST([Class]Test, [constraintName]_negative) {
    ...
}
// 如有边界条件：
TEST([Class]Test, [constraintName]_boundary) {
    ...
}

// R2: [规则描述]
...
</stage3>

<stage4>
## 审查结果
[表格...]

## 总体评估
[一段话]
</stage4>
```
