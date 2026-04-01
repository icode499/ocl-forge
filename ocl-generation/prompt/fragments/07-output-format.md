## 输出格式

严格按以下 XML 标签分隔四个阶段的输出。不要在标签外输出任何内容。

```xml
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
