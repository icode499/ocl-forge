# OCL 代码生成系统概要设计

## 1. 项目背景与目标

### 1.1 背景

当前拥有 100 个 OMG OCL（Object Constraint Language）样例，每个样例包含：
- 业务描述文本（内嵌 UML 模型信息：类、属性、关联关系）
- 对应的 OCL 约束代码
- C++ 业务测试代码（语法验证 + 业务逻辑验证）

这些样例可作为 prompt few-shot 参考和 RAG 检索语料，但数量仍偏少，必须通过明确的范围控制和质量闭环来提升生成稳定性。

### 1.2 v1 目标

构建一个轻量化的 OCL 生成能力，输入一段带有业务描述的文本，输出：
1. 符合业务逻辑的 OCL `inv` 约束代码
2. 对应的 C++ 业务测试代码
3. 可人工审查的结构化中间表示和自我审查结果

### 1.3 核心痛点

| 痛点 | 描述 |
|------|------|
| 样例少 | 仅 100 个样例，难以覆盖所有业务场景 |
| 业务逻辑不准确 | 生成的 OCL 语法正确但不符合预期业务语义 |
| 测试生成困难 | 不知道如何自动生成能验证业务逻辑的测试代码 |
| 输入歧义高 | 用户提供的业务文本常缺少必要 UML 细节，容易导致模型臆造 |

### 1.4 设计约束

- 轻量化交付：核心能力以 prompt template 形式交付，不依赖特定平台
- RAG 独立部署：样例检索服务作为独立仓库，提供 HTTP API
- 通用性：prompt template 可在任意商业大模型（Claude、GPT 等）中使用
- 不臆造：当输入缺少必要模型信息时，必须显式标记缺口，不得自行补全不存在的类、属性、关联
- 分层交付：prompt 负责生成与自我审查；编译执行验证属于可选的上层 agent/workflow 集成，不属于可移植 prompt 本身

### 1.5 v1 范围与非目标

**v1 明确支持：**
- `context <Class> inv <name>: <expr>` 形式的不变量约束
- 基于类、属性、关联、枚举的业务规则翻译
- 生成正例、反例及必要的边界例测试
- 通过 Few-shot + RAG 提升 invariant 生成质量

**v1 明确不支持：**
- `pre` / `post` / `body` / `def` / `init` 等操作级或派生级约束自动生成
- 需要操作签名、参数、返回值、`@pre` 状态建模的场景
- 在纯 prompt 环境中自动编译、运行、修复测试代码

**原因：**
`pre/post` 约束需要额外的操作元数据和执行前后状态建模，而当前 100 个样例的数据整理、测试 harness 以及输入契约尚未标准化到可稳定支持该能力。为避免范围漂移，v1 只聚焦 `inv`。

## 2. 系统架构

### 2.1 整体组成

系统由两个必选交付物和一个可选集成层组成：

```text
┌─────────────────────────────────────────────────────┐
│               使用时的完整 Prompt                    │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ System Prompt                                 │  │
│  │ - 角色定义 + OCL 语法规范摘要                  │  │
│  │ - 四阶段生成指令                               │  │
│  │ - C++ 测试 harness 契约                        │  │
│  │ - 自我审查规则                                 │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Few-shot 样例区                                │  │
│  │ - 固定区：5 个 Golden Examples                  │  │
│  │ - 动态区：RAG 检索的 1-2 个相似样例             │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ User Input                                     │  │
│  │ - 业务描述                                      │  │
│  │ - UML 结构信息                                  │  │
│  │ - 约束需求                                      │  │
│  └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
             │                           ▲
             ▼                           │
┌──────────────────────┐      ┌─────────────────────────┐
│ 大模型（任意）         │      │ RAG 服务（独立仓库）      │
│ 1. 结构化理解          │◀─────│ POST /api/v1/search     │
│ 2. OCL inv 代码       │      │ 输入：业务描述 + 结构摘要  │
│ 3. C++ 测试代码       │      │ 输出：相似样例            │
│ 4. 自我审查           │      └─────────────────────────┘
└──────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────┐
│ 可选执行层（非 prompt 交付物）                      │
│ 具备工具调用能力的 agent/workflow 可额外执行：       │
│ - 编译测试                                           │
│ - 运行测试                                           │
│ - 收集日志并触发人工或自动修复                       │
└─────────────────────────────────────────────────────┘
```

### 2.2 交付物

| 交付物 | 形式 | 说明 |
|--------|------|------|
| `ocl-generation-prompt/` | Prompt template 文件 + 使用说明 | 核心生成能力，不依赖特定平台 |
| `ocl-rag-service/` | 独立仓库，Python HTTP 服务 | 样例向量化检索，提供 API |
| `ocl-generation-runner/`（可选） | Agent/workflow 集成脚本 | 仅在具备工具调用的环境下执行编译与测试，不属于 prompt v1 必选交付物 |

## 3. Prompt Template 设计

### 3.1 System Prompt 结构

Prompt 引导大模型按四个阶段逐步输出，每个阶段有明确的输入输出格式。

```text
System Prompt 组成：

┌─ 角色定义 ─────────────────────────────────────────┐
│ 你是 OCL 代码生成专家，精通 OMG OCL 2.4 规范。      │
│ v1 只生成 invariant（inv）约束。                    │
└────────────────────────────────────────────────────┘
       │
┌─ OCL 语法规范摘要 ─────────────────────────────────┐
│ - v1 必须掌握 inv、集合操作、导航表达式、类型操作   │
│ - 可附带完整 OCL 2.4 参考，但生成指令必须明确：     │
│   当前任务只输出 inv                               │
│ - 常见易错点清单                                   │
└────────────────────────────────────────────────────┘
       │
┌─ 四阶段生成指令 ───────────────────────────────────┐
│ (详见 3.2 节)                                      │
└────────────────────────────────────────────────────┘
       │
┌─ Few-shot 样例区 ─────────────────────────────────┐
│ 固定区：完整四阶段样例                              │
│ 动态区：可压缩的 RAG 样例                           │
└────────────────────────────────────────────────────┘
       │
┌─ 输出格式约束 ─────────────────────────────────────┐
│ <stage1>...</stage1>                               │
│ <stage2>...</stage2>                               │
│ <stage3>...</stage3>                               │
│ <stage4>...</stage4>                               │
└────────────────────────────────────────────────────┘
```

### 3.1.1 输入契约（v1）

v1 不接受完全自由文本作为唯一输入。用户提供的业务描述至少应覆盖以下信息：

| 信息项 | 是否必需 | 说明 |
|--------|----------|------|
| 类列表 | 必需 | 至少给出上下文类及相关类名称 |
| 属性列表 | 必需 | 每个约束涉及的属性名与类型 |
| 关联关系 | 必需 | 关联名、方向、多重性 |
| 枚举定义 | 条件必需 | 约束涉及枚举时必须提供枚举值 |
| 业务规则 | 必需 | 用自然语言说明每条约束 |
| 规则上下文类 | 必需 | 每条规则属于哪个类 |

推荐输入模板：

```text
【类与属性】
- Order(totalAmount: Real, status: OrderStatus)
- OrderItem(quantity: Integer, unitPrice: Real)

【关联】
- Order.items -> OrderItem [1..*]

【枚举】
- OrderStatus = {draft, paid, cancelled}

【业务规则】
- R1: Order.totalAmount 必须等于所有 OrderItem 的 quantity * unitPrice 之和
- R2: OrderItem.quantity 必须大于 0
```

如果输入缺少必需信息：
- 阶段 1 必须输出 `信息缺口` 表格，列出缺失字段及影响范围
- 阶段 2 不得为受影响规则生成 OCL，必须标注 `SKIPPED_PENDING_CLARIFICATION`
- 阶段 3 不得为受影响规则生成测试，必须标注 `TEST_SKIPPED_PENDING_CLARIFICATION`

### 3.2 四阶段生成指令

#### 阶段 1：结构化理解

目的：迫使模型先理解业务语义再生成代码，解决“语法对但逻辑错”的核心问题。

输入：用户提供的业务描述文本和 UML 结构信息。

输出要求：
- 提取所有类、属性（含类型）、关联关系，以 Markdown 表格呈现
- 提取所有枚举类型及其值
- 将业务约束拆解为编号的自然语言规则列表（如 R1, R2, R3...）
- 每条规则必须标注：约束类型、上下文类、涉及的属性/关联
- v1 中约束类型仅允许 `inv`
- 如果信息不足，必须增加 `信息缺口` 表格

输出格式示例：

```text
<stage1>
## 模型结构

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|
| Order | totalAmount | Real | 订单总金额 |
| Order | status | OrderStatus | 订单状态 |
| OrderItem | quantity | Integer | 商品数量 |
| OrderItem | unitPrice | Real | 商品单价 |

## 关联关系

| 源类 | 目标类 | 关联名 | 多重性 |
|------|--------|--------|--------|
| Order | OrderItem | items | 1..* |

## 业务约束规则

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|
| R1 | inv | Order | totalAmount, items, quantity, unitPrice | 订单总金额必须等于所有订单项金额之和 |
| R2 | inv | OrderItem | quantity | 商品数量必须大于 0 |

## 信息缺口

| 规则 | 缺失信息 | 影响 |
|------|----------|------|
| 无 | - | - |
</stage1>
```

#### 阶段 2：OCL 生成

输入：阶段 1 的结构化理解结果。

输出要求：
- 逐条将业务规则翻译为 OCL `inv` 约束
- 每条 OCL 前标注对应的业务规则编号（R1, R2...），建立可追溯性
- 必须使用阶段 1 提取的类名、属性名、关联名，不得臆造不存在的元素
- 遵循 OMG OCL 2.4 语法规范
- 对存在信息缺口的规则输出 `SKIPPED_PENDING_CLARIFICATION`

输出格式示例：

```ocl
<stage2>
-- R1: 订单总金额必须等于所有订单项金额之和
context Order
inv totalAmountConsistency:
  self.totalAmount = self.items->collect(i | i.quantity * i.unitPrice)->sum()

-- R2: 商品数量必须大于 0
context OrderItem
inv positiveQuantity:
  self.quantity > 0
</stage2>
```

#### 阶段 3：C++ 测试生成

输入：阶段 1 的模型结构 + 阶段 2 的 OCL 代码。

输出要求：
- 为每条 OCL 约束生成一组测试
- 每条规则至少包含：
  - 正例（positive）：构造满足约束的对象实例，断言求值为 `true`
  - 反例（negative）：构造违反约束的对象实例，断言求值为 `false`
  - 边界例（boundary）：仅在存在明确边界条件时生成
- 边界测试判定标准：当约束包含比较运算符（`>`, `>=`, `<`, `<=`, `=`）或集合基数约束时，视为存在明确边界。边界例应使用恰好在阈值上的值（如 `> 0` 的边界值为 `0`），反例应使用明确违反约束的典型非法值（如 `> 0` 的反例为 `-1`）
- 测试数据必须与阶段 1 的模型结构一致
- 必须遵循 3.4 节规定的统一测试 harness 契约
- 对存在信息缺口的规则输出 `TEST_SKIPPED_PENDING_CLARIFICATION`

输出格式示例：

```cpp
<stage3>
// R1: 订单总金额必须等于所有订单项金额之和
TEST(OrderTest, totalAmountConsistency_positive) {
    Order order;
    OrderItem item1, item2;
    item1.setQuantity(2);
    item1.setUnitPrice(10.0);
    item2.setQuantity(1);
    item2.setUnitPrice(20.0);
    order.addItem(item1);
    order.addItem(item2);
    order.setTotalAmount(40.0);  // 2*10 + 1*20 = 40
    ASSERT_TRUE(evaluate(order, "totalAmountConsistency"));
}

TEST(OrderTest, totalAmountConsistency_negative) {
    Order order;
    OrderItem item1;
    item1.setQuantity(2);
    item1.setUnitPrice(10.0);
    order.addItem(item1);
    order.setTotalAmount(999.0);  // 不等于 2*10 = 20
    ASSERT_FALSE(evaluate(order, "totalAmountConsistency"));
}

// R2: 商品数量必须大于 0
TEST(OrderItemTest, positiveQuantity_positive) {
    OrderItem item;
    item.setQuantity(1);
    ASSERT_TRUE(evaluate(item, "positiveQuantity"));
}

TEST(OrderItemTest, positiveQuantity_negative) {
    OrderItem item;
    item.setQuantity(-1);
    ASSERT_FALSE(evaluate(item, "positiveQuantity"));
}

TEST(OrderItemTest, positiveQuantity_boundary) {
    OrderItem item;
    item.setQuantity(0);  // 恰好在阈值上：quantity > 0，故 0 不满足
    ASSERT_FALSE(evaluate(item, "positiveQuantity"));
}
</stage3>
```

#### 阶段 4：自我审查

阶段 4 只负责审查，不负责执行外部命令。

审查要求：
- 逐条检查 OCL 语法正确性
- 逐条检查 OCL 是否准确表达了对应的业务规则（R1, R2...）
- 检查测试用例是否覆盖正例、反例、边界情况
- 检查测试数据与模型结构的一致性
- 对每条规则给出置信度（高/中/低）和潜在风险点
- 对于 `SKIPPED_PENDING_CLARIFICATION` 规则，明确指出需要补充的输入信息

输出格式示例：

```text
<stage4>
## 审查结果

| 规则 | OCL 语法 | 业务逻辑 | 测试覆盖 | 置信度 | 风险点 |
|------|----------|----------|----------|--------|--------|
| R1 | ✓ | ✓ | 正例+反例 | 高 | 无 |
| R2 | ✓ | ✓ | 正例+反例+边界 | 高 | 无 |

## 总体评估
所有约束语法正确，业务逻辑与规则描述一致，测试覆盖充分。
</stage4>
```

### 3.3 Few-shot 样例区设计

样例区分为固定区和 RAG 动态区，两者互补。

**固定区（Golden Examples）：**
- 必须完整展示四个阶段输出（结构化理解 -> OCL -> 测试 -> 审查）
- 从 100 个样例中精选 5 个，覆盖最常见的 invariant 模式：
  1. 简单属性约束
  2. 集合量词约束（`forAll` / `exists` / `select`）
  3. 关联导航约束
  4. 枚举状态条件约束（`implies` / `if-then-else`）
  5. 复合聚合约束（`collect` / `sum` / `let`）

**RAG 动态区：**
- 默认放置 1-2 个最相似样例
- 为节省 token，允许使用压缩格式：
  - 必需：阶段 2（OCL）、阶段 3（测试）
  - 可选：一行阶段 1 结构摘要、阶段 4 风险结论
- RAG 不可用时此区为空，不影响基本生成能力

固定区样例选取标准：
- 从 100 个样例中对 invariant 模式做聚类
- 每类选出最具代表性、复杂度适中的 1 个
- 优先选择业务语义清晰、测试覆盖完整的样例

### 3.4 C++ 测试 harness 契约

阶段 3 生成的测试必须面向一个统一的、先验约定好的测试 harness。该 harness 不是“示意”，而是 v1 发布前必须抽取并固化的契约。

统一契约至少包含：
- 固定的测试框架与断言宏（如 `TEST` / `ASSERT_TRUE` / `ASSERT_FALSE`）
- 固定的约束求值入口（如 `evaluate(obj, "<constraint_name>") -> bool`）
- 固定的对象构造和关联建立方式
- 固定的头文件、命名空间和 fixture 约定

测试模板骨架：

```cpp
// 正例：构造满足约束的对象，断言通过
TEST(<ContextClass>Test, <ConstraintName>_positive) {
    <ContextClass> obj;
    // 设置满足约束的属性值
    obj.set<Attr>(validValue);
    ASSERT_TRUE(evaluate(obj, "<constraint_name>"));
}

// 反例：构造违反约束的对象，断言不通过
TEST(<ContextClass>Test, <ConstraintName>_negative) {
    <ContextClass> obj;
    // 设置违反约束的属性值
    obj.set<Attr>(invalidValue);
    ASSERT_FALSE(evaluate(obj, "<constraint_name>"));
}

// 边界例（可选）：构造处于约束边界的对象
TEST(<ContextClass>Test, <ConstraintName>_boundary) {
    <ContextClass> obj;
    obj.set<Attr>(boundaryValue);
    ASSERT_<TRUE|FALSE>(evaluate(obj, "<constraint_name>"));
}
```

发布门槛：
- 在 `cpp-test-template.md` 中必须落入一个真实、唯一、可执行的模板
- 若尚未从现有 100 个测试中抽取出统一 harness，则阶段 3 的输出仅可视为“待适配骨架”，不得宣称可直接编译执行

## 4. RAG 样例检索服务

### 4.1 职责

独立仓库 `ocl-rag-service/`，职责单一：输入业务描述文本和结构摘要，返回最相似的 invariant 样例。

### 4.2 接口契约

```json
POST /api/v1/search

Request:
{
  "query": "业务描述文本...",
  "context_summary": "Order(totalAmount: Real) --items[1..*]--> OrderItem(quantity: Integer, unitPrice: Real)",
  "top_k": 2,
  "min_score": 0.5
}

Response:
{
  "results": [
    {
      "id": "sample_042",
      "score": 0.87,
      "description": "原始业务描述文本...",
      "context_summary": "Order(totalAmount: Real) --items[1..*]--> OrderItem(quantity: Integer, unitPrice: Real)",
      "pattern_tags": ["collection", "sum", "navigation"],
      "ocl": "context Order inv: ...",
      "test_code": "TEST(OrderTest, ...) { ... }",
      "stage1_ir": "..."
    }
  ]
}
```

说明：
- 请求中 `context_summary` 为可选字段，传入时用于提升检索相关性（参与 rerank 阶段的结构相似度计算）；不传时仅基于 `query` 做语义检索
- 响应中 `context_summary` 和 `pattern_tags` 为可选字段，但 v1 推荐返回，用于改善样例拼装质量
- 默认 `top_k = 2`，避免 RAG 区 token 失控

### 4.3 内部实现要点

- 100 个样例做结构化存储：`description + normalized stage1_ir + pattern_tags + ocl + test_code`
- 检索不应只依赖 `description` embedding
- 推荐两阶段策略：
  1. 召回：基于 `description` 和 `stage1_ir` 做语义检索
  2. 重排：结合类名重叠、关联结构相似度、`pattern_tags` 相似度进行 rerank
- `ocl` 和 `test_code` 主要用于样例展示与人工复核，不作为唯一召回依据
- 后续样例增加时只需追加索引，不影响 prompt 侧
- 技术选型由 RAG 仓库独立决定（推荐轻量方案如 FAISS + FastAPI）

### 4.4 降级策略

RAG 服务不可用时，prompt 仍可工作：
- 用户手动选择相关样例粘贴到 Few-shot 动态区
- 固定区 Golden Examples 保证基本生成质量
- 当 RAG 缺失导致相似模式覆盖不足时，阶段 4 必须提高风险提示级别

## 5. 前置工作

在 prompt template 可用之前，需要完成以下准备工作：

| 序号 | 工作项 | 说明 | 产出 | 优先级 |
|------|--------|------|------|--------|
| 1 | invariant 模式聚类 | 对 100 个样例的 OCL 代码做模式分类 | 5-8 个 invariant 模式类别 | P0 |
| 2 | Golden Examples 选取 | 每类选 1 个最具代表性的样例（依赖 #1） | 5 个固定样例 | P0 |
| 3 | C++ 测试 harness 固化 | 从 100 个测试中抽象唯一可执行模板 | 统一测试模板代码 | P0 |
| 4 | OCL 语法规范摘要 | 整理 OMG OCL 2.4 核心语法速查 | 语法参考文本 | P0 |
| 5 | 输入模板与缺口策略 | 固化用户输入模板和缺失信息处理规则 | 输入契约文本 | P0 |
| 6 | Golden Examples 四阶段化 | 为每个固定样例补充完整四阶段输出（依赖 #2, #3） | 可直接嵌入 prompt 的样例文本 | P1 |
| 7 | 常见易错点整理 | 从现有样例中总结 OCL 生成的常见错误 | 易错点清单 | P1 |
| 8 | 评测集与基线建立 | 划分 holdout 集并建立 no-RAG 基线 | 评测报告与指标基线 | P1 |

### 5.1 Token 预算考量

固定区 5 个完整四阶段样例 + RAG 动态区 1-2 个样例，token 消耗较大。控制策略：

- 固定区样例选择复杂度适中的，避免过长的 OCL 或测试代码
- 固定区样例的阶段 4 可精简为一行结论，不展开完整表格
- RAG 动态区默认只展示阶段 2 和阶段 3，必要时附一行结构摘要
- 如果总 token 仍然超限，优先保留固定区，缩减 RAG 区到 1 个样例

## 6. 质量保障与验收标准

### 6.1 业务逻辑准确性保障

通过多层机制保障：

1. **阶段 1 结构化理解**：迫使模型先理解再生成，中间表示可人工审查
2. **信息缺口显式化**：缺信息时停止生成，不允许猜测
3. **规则编号追溯**：每条 OCL 标注对应的业务规则编号，方便定位问题
4. **固定区样例**：覆盖常见 invariant 模式，减少模型随意发挥
5. **RAG 动态样例**：提供与当前场景最相关的参考
6. **阶段 4 自我审查**：显式输出置信度和风险点

### 6.2 测试生成质量保障

1. **统一 C++ harness 契约**：避免生成面向不同测试风格的代码
2. **正例 + 反例 + 条件性边界例**：确保约束行为可验证
3. **模型结构一致性**：测试数据必须使用阶段 1 提取的类、属性、关联
4. **发布门槛约束**：未固化真实 harness 前，不宣称测试代码可直接编译执行

### 6.3 v1 验收标准

使用从 100 个样例中分层抽取的 20 个 holdout 用例做离线评测，至少达到：

| 指标 | 定义 | 通过线 |
|------|------|--------|
| Stage1 完整率 | 必需类/属性/关联/枚举被正确提取的比例 | >= 95% |
| 禁止臆造通过率 | 未使用输入中不存在元素的规则占比 | >= 98% |
| OCL 语法通过率 | 约束能通过语法检查或人工语法审查 | >= 95% |
| 规则语义通过率 | OCL 与规则描述语义一致的规则占比 | >= 85% |
| 测试覆盖率 | 每条成功生成的规则均具备正例和反例 | = 100% |
| 边界例充分率 | 存在明确边界的规则中，生成边界例的占比 | >= 90% |
| 编译通过率 | 在统一 harness 上，生成测试可编译通过的用例占比 | >= 85% |
| RAG 收益 | 相比 no-RAG 基线，语义通过率提升 | >= 10 个百分点 |

说明：
- `编译通过率` 仅在统一 harness 固化后纳入正式验收
- 若 `禁止臆造通过率` 不达标，则无论其他指标如何，v1 均不得上线

### 6.4 可选执行验证集成

如果后续接入具备工具调用能力的 agent/workflow，可在 prompt 输出之后增加执行闭环：

1. 将阶段 3 生成的测试代码写入临时工程
2. 调用编译命令执行测试
3. 收集编译错误和失败用例
4. 触发人工修正或有限次自动重试

该流程是上层集成能力，不属于 prompt v1 的规范边界，必须与 prompt 文本分层实现。

## 7. 使用流程

```text
用户视角的使用流程：

1. 按输入模板准备业务描述文本（包含 UML 模型信息和约束需求）
2. [可选] 调用 RAG 服务获取 1-2 个相似样例
3. 将 System Prompt + 固定样例 + RAG 样例 + 业务描述组装为完整 prompt
4. 发送给大模型
5. 获得四阶段输出：结构化理解 -> OCL -> 测试 -> 审查报告
6. 先审查 stage1 的结构化理解和信息缺口
7. 再审查 stage4 的风险点和置信度
8. 最后查看 stage2 / stage3 是否满足业务预期
9. 如有可选执行层，再进行编译和运行验证
```

## 8. 版本管理

为确保可追溯性，以下产物必须携带版本标识：

| 产物 | 版本格式 | 说明 |
|------|----------|------|
| Prompt Template | `prompt-v<major>.<minor>` | 修改生成指令、阶段定义、system prompt 结构时递增 major；修改样例、措辞时递增 minor |
| Golden Examples 集 | `golden-v<N>` | 更换或新增固定样例时递增 |
| RAG 样例索引 | `index-v<N>` | 重建索引或样例集变更时递增 |
| C++ 测试 harness | `harness-v<N>` | 修改 harness 契约时递增 |

生成结果应记录所用版本组合（如 `prompt-v1.2 + golden-v1 + index-v3 + harness-v1`），用于离线评测结果归因和回归对比。

## 9. 后续演进方向

- **pre/post 支持**：在补齐操作签名、参数、返回值和 `@pre` 状态建模后，扩展到操作级约束
- **样例扩增**：用大模型基于现有样例生成变体，人工审核后加入 RAG
- **Claude Code Skill 化**：将 prompt template 封装为 Claude Code skill，自动化 RAG 调用和测试执行
- **MCP Server 化**：将 RAG 服务封装为 MCP Server，大模型可直接调用
- **反馈学习**：收集用户修正记录，优化 prompt 和样例选取策略
