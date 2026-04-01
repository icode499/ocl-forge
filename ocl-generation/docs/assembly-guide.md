# OCL Generation Prompt 组装和使用指南

## 三种使用方式

### 方式 1：直接使用（无 RAG）

1. 打开 `prompt/system-prompt.md`
2. 将全部内容复制为大模型的 system prompt
3. 在 user message 中按输入模板格式提供业务描述
4. 获得四阶段输出

适用场景：没有 RAG 服务，或临时使用。

### 方式 2：配合 RAG 服务

1. 调用 RAG 服务获取相似样例：

```bash
curl -X POST http://<rag-service>/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "你的业务描述文本",
    "context_summary": "Class1(attr: Type) --assoc[*]--> Class2(attr: Type)",
    "top_k": 2,
    "min_score": 0.5
  }'
```

2. 将返回的样例填入 system prompt 的「RAG 动态样例区」
3. 发送给大模型

### 方式 3：手动选择样例

1. 浏览样例库，找到与当前场景最相似的 1-2 个样例
2. 将样例的 OCL 代码和测试代码粘贴到「RAG 动态样例区」
3. 发送给大模型

## 输入格式

业务描述文本必须包含 UML 模型信息。推荐格式：

```text
【类与属性】
- Employee(name: String, age: Integer, salary: Real)
- Department(name: String, budget: Real)

【关联】
- Employee.department -> Department [1]
- Department.employees -> Employee [1..*]

【枚举】
- EmployeeStatus = {active, onLeave, terminated}

【业务规则】
- R1: 员工年龄必须在 18 到 65 之间
- R2: 员工薪资不能超过所在部门预算的 50%
- R3: 每个部门至少有一名员工
```

## 输出说明

大模型会输出四个 XML 标签包裹的阶段：

| 标签 | 内容 | 审查优先级 |
|------|------|-----------|
| `<stage1>` | 结构化理解（模型结构 + 规则列表 + 信息缺口） | **先看这里** |
| `<stage2>` | OCL inv 约束代码 | 确认 stage1 无误后看 |
| `<stage3>` | C++ 测试代码 | 确认 stage2 无误后看 |
| `<stage4>` | 自我审查报告（置信度 + 风险点） | **然后看这里** |

## 审查建议

1. **先看 stage1**：模型结构是否完整？信息缺口是否合理？
2. **再看 stage4**：风险点和置信度是否可接受？
3. **再看 stage2**：OCL 是否准确表达业务规则？
4. **最后看 stage3**：测试是否合理？

如果 stage1 有遗漏或错误，后续阶段的输出都不可信——修正输入后重新生成。

## Token 预算控制

如果遇到上下文长度限制：

| 优先级 | 缩减策略 |
|--------|----------|
| 1 | RAG 动态区从 2 个样例缩减到 1 个 |
| 2 | RAG 动态区只保留阶段 2（OCL），去掉阶段 3（测试） |
| 3 | 移除 RAG 动态区，仅依赖固定样例 |
| 4 | 固定样例从 5 个缩减到 3 个（保留 #1 属性、#2 集合、#5 复合） |

不要缩减 fragments 区（角色定义、语法速查、阶段指令等），这些是生成质量的基础。

## 版本追踪

记录每次生成使用的版本组合，用于评测结果归因：

```text
prompt-v1.0 + golden-v1 + index-v3 + harness-v1
```

详见根目录 `VERSION` 文件。
