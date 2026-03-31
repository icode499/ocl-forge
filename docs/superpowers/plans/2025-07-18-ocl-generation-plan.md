# OCL 代码生成系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个轻量化的 prompt template，引导大模型按四阶段流程生成 OCL `inv` 约束代码和 C++ 测试代码，配合独立的 RAG 样例检索服务接口契约。

**Architecture:** 核心是一个多阶段 prompt template（结构化理解 → OCL inv 生成 → 测试生成 → 自我审查），配合固定 5 个 Golden Examples + RAG 动态 1-2 个的 few-shot 样例区。RAG 服务独立仓库，本项目仅定义接口契约（OpenAPI 3.0）。输入强制要求结构化 UML 信息，缺失时停止生成并标记缺口。

**Tech Stack:** Prompt engineering（纯文本 Markdown），OpenAPI 3.0（RAG 接口契约），YAML

**Spec reference:** `docs/superpowers/specs/2025-07-18-ocl-generation-design.md`

---

## 文件结构

```
ocl-generation/
├── prompt/
│   ├── system-prompt.md              # 完整的 system prompt（最终交付物，由 fragments 组装）
│   ├── fragments/
│   │   ├── 01-role-definition.md     # 角色定义 + v1 范围声明
│   │   ├── 02-ocl-syntax-reference.md # OCL 2.4 核心语法速查（仅 inv 相关重点标注）
│   │   ├── 03-common-mistakes.md     # 常见易错点清单
│   │   ├── 04-input-contract.md      # 输入契约 + 信息缺口处理规则
│   │   ├── 05-stage-instructions.md  # 四阶段生成指令（仅 inv）
│   │   ├── 06-cpp-test-template.md   # C++ 测试 harness 契约 + 边界测试标准
│   │   └── 07-output-format.md       # 输出格式约束（XML 标签）
│   └── examples/
│       ├── README.md                 # Golden Examples 选取指南与操作步骤
│       ├── golden-01-attribute.md    # 简单属性约束（如 age > 0）
│       ├── golden-02-collection.md   # 集合量词约束（forAll/exists/select）
│       ├── golden-03-navigation.md   # 关联导航约束（跨对象引用）
│       ├── golden-04-enum-condition.md # 枚举状态条件约束（implies/if-then-else）
│       └── golden-05-compound.md     # 复合聚合约束（collect/sum/let）
├── rag-contract/
│   └── openapi.yaml                  # RAG 服务 OpenAPI 3.0 接口定义
├── docs/
│   └── assembly-guide.md             # Prompt 组装和使用指南
├── VERSION                           # 版本标识文件
└── README.md                         # 项目说明
```

说明：
- `prompt/fragments/` 按编号排序，对应组装顺序
- `golden-04` 是枚举条件约束（implies/if-then-else），不是 pre/post（v1 不支持）
- `prompt/system-prompt.md` 是 fragments + examples 的组装产物，直接可用
- Golden Examples 需要从 100 个样例中选取填充（Task 7 提供选取指南和模板骨架）
- 版本管理详见 spec 第 8 节

---

### Task 1: 项目脚手架

**Files:**
- Create: `ocl-generation/README.md`
- Create: `ocl-generation/VERSION`
- Create: `ocl-generation/prompt/fragments/` (directory)
- Create: `ocl-generation/prompt/examples/` (directory)
- Create: `ocl-generation/rag-contract/` (directory)
- Create: `ocl-generation/docs/` (directory)

- [ ] **Step 1: 创建目录结构**

```bash
cd /home/hyz/code/prodEng/ocl-forge
mkdir -p ocl-generation/prompt/fragments ocl-generation/prompt/examples ocl-generation/rag-contract ocl-generation/docs
```

- [ ] **Step 2: 创建版本标识文件**

Write to `ocl-generation/VERSION`:

```text
prompt-v1.0
golden-v0 (pending selection)
index-v0 (pending RAG deployment)
harness-v0 (pending extraction from existing tests)
```

- [ ] **Step 3: 创建项目 README**

Write to `ocl-generation/README.md`:

```markdown
# OCL Generation Prompt Template

利用大模型按四阶段流程生成 OMG OCL `inv` 约束代码和 C++ 业务测试代码的 prompt template。

## v1 范围

- 仅支持 `context <Class> inv <name>: <expr>` 形式的不变量约束
- 不支持 `pre` / `post` / `body` / `def` / `init`

## 项目结构

- `prompt/system-prompt.md` — 完整的 system prompt，直接可用
- `prompt/fragments/` — prompt 各片段，按编号排序，独立维护
- `prompt/examples/` — Few-shot Golden Examples（需从样例库选取填充）
- `rag-contract/openapi.yaml` — RAG 样例检索服务接口定义
- `docs/assembly-guide.md` — 组装和使用指南
- `VERSION` — 版本标识

## 快速开始

参见 `docs/assembly-guide.md`

## 版本管理

参见 `VERSION` 文件和设计文档第 8 节。
```

- [ ] **Step 4: 提交**

```bash
git add ocl-generation/
git commit -m "chore: init ocl-generation project structure with version tracking"
```

---

### Task 2: 角色定义片段

**Files:**
- Create: `ocl-generation/prompt/fragments/01-role-definition.md`

- [ ] **Step 1: 编写角色定义**

Write to `ocl-generation/prompt/fragments/01-role-definition.md`:

```markdown
## 角色定义

你是一个 OCL（Object Constraint Language）代码生成专家，精通 OMG OCL 2.4 规范。

**v1 范围限制：你只生成 invariant（`inv`）约束。不要生成 `pre`、`post`、`body`、`def`、`init` 等其他约束类型。** 如果用户的业务规则需要操作级约束（如前置条件、后置条件），在阶段 1 的信息缺口表中标注，阶段 2 输出 `SKIPPED_OUT_OF_V1_SCOPE`。

你的职责是：
1. 理解用户提供的业务描述文本（包含 UML 模型信息和业务约束需求）
2. 按四个阶段逐步输出：结构化理解 → OCL inv 代码 → C++ 测试代码 → 自我审查
3. 确保生成的 OCL 严格符合语法规范，且准确表达业务语义
4. 确保生成的测试代码能有效验证 OCL 约束的正确性

关键原则：
- **先理解，再生成**：不要跳过阶段 1 直接写 OCL
- **不臆造**：只使用用户输入中明确声明的类、属性、关联、枚举，不得自行补全
- **可追溯**：每条 OCL 约束必须标注对应的业务规则编号（R1, R2...）
- **缺口显式化**：输入缺少必要信息时，在阶段 1 标记缺口，后续阶段对受影响规则输出 SKIPPED 标记
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/prompt/fragments/01-role-definition.md
git commit -m "feat: add role definition with v1 scope constraint"
```

---

### Task 3: OCL 语法规范速查

**Files:**
- Create: `ocl-generation/prompt/fragments/02-ocl-syntax-reference.md`

- [ ] **Step 1: 编写 OCL 2.4 核心语法速查**

Write to `ocl-generation/prompt/fragments/02-ocl-syntax-reference.md`:

```markdown
## OCL 2.4 语法规范速查

> v1 只生成 `inv` 约束。其他约束类型（pre/post/body/def/init）列出仅供参考，不要在输出中使用。

### 约束类型

- **`context <Class> inv <name>: <expr>`** — 不变量，任何时刻都必须为 true **（v1 唯一输出类型）**
- `context <Class>::<op>(<params>) pre <name>: <expr>` — 前置条件（v1 不支持）
- `context <Class>::<op>(<params>) post <name>: <expr>` — 后置条件（v1 不支持）
- `context <Class>::<op>(<params>): <Type> body <name>: <expr>` — 操作体定义（v1 不支持）
- `context <Class> def <name>: <Type> = <expr>` — 辅助定义（v1 不支持）
- `context <Class> init <name>: <expr>` — 初始值（v1 不支持）

### 基本表达式

- `self` — 当前上下文对象
- `self.<attr>` — 访问属性
- `self.<assoc>` — 导航关联（返回集合或单个对象，取决于多重性）
- `self.<op>(<args>)` — 调用操作

### 类型系统

- 基本类型：`Boolean`, `Integer`, `Real`, `String`, `UnlimitedNatural`
- 集合类型：`Set(T)`, `Bag(T)`, `Sequence(T)`, `OrderedSet(T)`, `Collection(T)`
- 特殊值：`null`, `invalid`, `OclVoid`, `OclInvalid`

### 集合操作

- `->size()` — 集合大小
- `->isEmpty()` / `->notEmpty()` — 空/非空判断
- `->includes(obj)` / `->excludes(obj)` — 包含/不包含
- `->forAll(v | expr)` — 所有元素满足条件
- `->exists(v | expr)` — 存在元素满足条件
- `->select(v | expr)` — 筛选满足条件的元素
- `->reject(v | expr)` — 排除满足条件的元素
- `->collect(v | expr)` — 映射转换
- `->any(v | expr)` — 返回任意一个满足条件的元素
- `->isUnique(v | expr)` — 表达式值唯一
- `->one(v | expr)` — 恰好一个元素满足条件
- `->sum()` — 数值集合求和
- `->flatten()` — 展平嵌套集合
- `->asSet()` / `->asBag()` / `->asSequence()` / `->asOrderedSet()` — 集合类型转换
- `->union(c)` / `->intersection(c)` — 集合运算
- `->including(obj)` / `->excluding(obj)` — 添加/移除元素

### 逻辑操作

- `and`, `or`, `not`, `xor`
- `implies` — 蕴含（`a implies b` 等价于 `not a or b`）
- `if <cond> then <expr1> else <expr2> endif` — 条件表达式

### 类型操作

- `oclIsTypeOf(Type)` — 精确类型判断
- `oclIsKindOf(Type)` — 类型及子类型判断
- `oclAsType(Type)` — 类型转换

### 字符串操作

- `.size()` — 字符串长度
- `.concat(s)` — 拼接
- `.substring(lower, upper)` — 子串（1-based）
- `.toInteger()` / `.toReal()` — 类型转换

### let 表达式

```ocl
context Order inv totalCheck:
  let total: Real = self.items->collect(i | i.quantity * i.unitPrice)->sum() in
  total > 0 and total <= self.maxAmount
```
```

- [ ] **Step 2: 验证语法覆盖度**

检查清单：
- 是否覆盖了 inv 约束语法（上下文声明、命名）
- 是否覆盖了所有集合操作（size/isEmpty/forAll/exists/select/reject/collect/sum 等）
- 是否包含 let 表达式
- 是否包含逻辑操作（implies/if-then-else）
- 是否包含类型操作（oclIsTypeOf/oclIsKindOf）
- 是否明确标注了 v1 不支持的约束类型

- [ ] **Step 3: 提交**

```bash
git add ocl-generation/prompt/fragments/02-ocl-syntax-reference.md
git commit -m "feat: add OCL 2.4 syntax quick reference with v1 scope markers"
```

---

### Task 4: 常见易错点清单

**Files:**
- Create: `ocl-generation/prompt/fragments/03-common-mistakes.md`

- [ ] **Step 1: 编写常见易错点**

Write to `ocl-generation/prompt/fragments/03-common-mistakes.md`:

```markdown
## OCL 生成常见易错点

生成 OCL 时必须避免以下错误：

### 语法层面

1. **集合操作用 `->` 不是 `.`**
   - 错误：`self.items.size()`
   - 正确：`self.items->size()`

2. **单个对象用 `.` 不是 `->`**
   - 错误：`self.owner->name`
   - 正确：`self.owner.name`

3. **forAll/exists 必须绑定迭代变量**
   - 错误：`self.items->forAll(quantity > 0)`
   - 正确：`self.items->forAll(i | i.quantity > 0)`

4. **collect 后的集合类型变化**
   - `Set->collect()` 返回 `Bag`，不是 `Set`
   - 如需去重，追加 `->asSet()`

5. **substring 是 1-based**
   - 错误：`s.substring(0, 3)`
   - 正确：`s.substring(1, 3)`

6. **inv 约束必须命名**
   - 错误：`context Order inv: self.total > 0`
   - 正确：`context Order inv positiveTotal: self.total > 0`

### 业务逻辑层面

7. **臆造不存在的属性或关联**
   - 必须严格使用阶段 1 提取的类名、属性名、关联名
   - 不得假设模型中未声明的元素
   - 如果发现需要但缺失的元素，回到阶段 1 的信息缺口表中记录

8. **多重性混淆**
   - 多重性为 `0..1` 的关联导航结果可能为 null，需要用 `<> null` 或 `oclIsUndefined()` 保护
   - 多重性为 `*` 或 `1..*` 的关联导航结果是集合，必须用 `->` 操作

9. **implies 的短路语义**
   - `a implies b`：当 a 为 false 时整个表达式为 true
   - 常用于条件约束：`self.status = #active implies self.balance >= 0`
   - 注意：这意味着 status 不是 active 的对象总是满足该约束

10. **集合操作链的空集处理**
    - `emptySet->forAll(...)` 返回 true（空集上的全称量词为真）
    - `emptySet->exists(...)` 返回 false
    - 如果业务上空集不合法，需要额外加 `->notEmpty()` 检查
    - 示例：`self.items->notEmpty() and self.items->forAll(i | i.quantity > 0)`
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/prompt/fragments/03-common-mistakes.md
git commit -m "feat: add common OCL generation mistakes guide"
```

---

### Task 5: 输入契约片段

**Files:**
- Create: `ocl-generation/prompt/fragments/04-input-contract.md`

- [ ] **Step 1: 编写输入契约和信息缺口处理规则**

Write to `ocl-generation/prompt/fragments/04-input-contract.md`:

```markdown
## 输入契约

用户输入的业务描述必须包含以下结构化信息：

| 信息项 | 是否必需 | 说明 |
|--------|----------|------|
| 类列表 | 必需 | 至少给出上下文类及相关类名称 |
| 属性列表 | 必需 | 每个约束涉及的属性名与类型 |
| 关联关系 | 必需 | 关联名、方向、多重性 |
| 枚举定义 | 条件必需 | 约束涉及枚举时必须提供枚举值 |
| 业务规则 | 必需 | 用自然语言说明每条约束 |
| 规则上下文类 | 必需 | 每条规则属于哪个类 |

### 推荐输入格式

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

### 信息缺口处理

如果用户输入缺少上述必需信息：

1. **阶段 1** 必须输出「信息缺口」表格：

| 规则 | 缺失信息 | 影响 |
|------|----------|------|
| R3 | Order 与 Customer 的关联多重性未声明 | 无法确定导航表达式返回类型 |

2. **阶段 2** 对受影响规则输出：
```
-- R3: [原始业务规则描述]
-- SKIPPED_PENDING_CLARIFICATION: 缺少 Order-Customer 关联多重性
```

3. **阶段 3** 对受影响规则输出：
```
// R3: TEST_SKIPPED_PENDING_CLARIFICATION
// 缺少 Order-Customer 关联多重性，无法生成测试
```

**关键原则：宁可跳过也不臆造。** 缺少信息时不得假设默认值或自行补全模型元素。
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/prompt/fragments/04-input-contract.md
git commit -m "feat: add input contract with info gap handling rules"
```

---

### Task 6: 四阶段生成指令

**Files:**
- Create: `ocl-generation/prompt/fragments/05-stage-instructions.md`

- [ ] **Step 1: 编写四阶段指令**

Write to `ocl-generation/prompt/fragments/05-stage-instructions.md`:

```markdown
## 四阶段生成指令

收到用户的业务描述文本后，严格按以下四个阶段依次输出。每个阶段的输出是下一个阶段的输入，不得跳过任何阶段。

---

### 阶段 1：结构化理解

从用户输入中提取以下信息，以 Markdown 表格呈现：

**1.1 模型结构**

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|

提取所有类及其所有属性。每个属性单独一行。

**1.2 关联关系**

| 源类 | 目标类 | 关联名 | 多重性 | 说明 |
|------|--------|--------|--------|------|

**1.3 枚举类型**（如有）

| 枚举名 | 值 |
|--------|-----|

**1.4 业务约束规则**

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|

规则编号格式：R1, R2, R3...
约束类型：仅限 `inv`。如果某条业务规则需要 pre/post 等操作级约束，在约束类型列标注 `OUT_OF_V1_SCOPE`。

「涉及属性/关联」必须列出该规则 OCL 表达式中将要使用的**所有**属性和关联名。阶段 2 只允许使用此处列出的元素。

**1.5 信息缺口**（如有）

| 规则 | 缺失信息 | 影响 |
|------|----------|------|

如无缺口，输出「无信息缺口」。

**检查点：** 输出阶段 1 后，自问：
- 模型结构表是否列全了所有类的所有属性？（不要遗漏——后续阶段只能使用这里列出的元素）
- 每条规则的「涉及属性/关联」是否完整？
- 是否有规则需要 pre/post，已标注 OUT_OF_V1_SCOPE？

---

### 阶段 2：OCL inv 生成

基于阶段 1 的结构化理解，逐条将 `inv` 类型的业务规则翻译为 OCL：

**规则：**
1. 每条 OCL 前用注释标注规则编号和自然语言描述：`-- R<N>: <描述>`
2. **必须且只能**使用阶段 1「涉及属性/关联」列中列出的元素，不得臆造
3. 为每条约束命名（`inv <name>:`），名称用驼峰命名，有业务含义
4. 遵循 OCL 语法规范速查中的语法规则
5. 避免常见易错点清单中列出的错误
6. 对阶段 1 标注 `OUT_OF_V1_SCOPE` 的规则输出 `SKIPPED_OUT_OF_V1_SCOPE`
7. 对存在信息缺口的规则输出 `SKIPPED_PENDING_CLARIFICATION`

**检查点：** 输出阶段 2 后，自问：
- 每条 OCL 是否都有对应的规则编号？
- 是否使用了阶段 1 模型结构表中不存在的属性或关联？
- 集合操作是否使用了 `->` 而非 `.`？
- `forAll`/`exists` 是否正确绑定了迭代变量？
- inv 是否都有命名？

---

### 阶段 3：C++ 测试生成

基于阶段 1 的模型结构和阶段 2 的 OCL 代码，为每条成功生成的约束生成测试：

**规则：**
1. 每条约束至少生成**正例**（positive）和**反例**（negative）两个测试
2. **边界例**（boundary）判定标准：当约束包含比较运算符（`>`, `>=`, `<`, `<=`, `=`）或集合基数约束（`->size() >= N`）时，视为存在明确边界条件，必须生成边界例
3. 边界例使用恰好在阈值上的值（如 `> 0` 的边界值为 `0`）；反例使用明确违反约束的典型非法值（如 `> 0` 的反例为 `-1`）
4. 遵循 C++ 测试模板的结构
5. 测试数据必须使用阶段 1 中的类和属性名
6. 每个测试值旁用注释说明为什么满足/违反约束
7. 对 SKIPPED 的规则输出 `TEST_SKIPPED_PENDING_CLARIFICATION` 或 `TEST_SKIPPED_OUT_OF_V1_SCOPE`

**检查点：** 输出阶段 3 后，自问：
- 每条成功生成的 OCL 约束是否都有对应的测试？
- 正例的测试数据是否确实满足约束？
- 反例的测试数据是否确实违反约束？
- 含比较运算符的约束是否都有边界例？
- 边界例的值是否恰好在阈值上（而非随意选取的非法值）？

---

### 阶段 4：自我审查

对阶段 2 和阶段 3 的输出进行系统性审查。

**注意：自我审查是辅助性检查，不能替代人工审查或编译验证。** 同一模型生成并审查存在系统性盲区，审查结果仅供参考。

**审查项目：**

| 规则 | OCL 语法 | 业务逻辑 | 测试覆盖 | 置信度 | 风险点 |
|------|----------|----------|----------|--------|--------|

- **OCL 语法**：✓ 或 ✗，是否符合 OCL 2.4 规范
- **业务逻辑**：✓ 或 ✗，OCL 是否准确表达了对应的业务规则
- **测试覆盖**：列出覆盖的类型（正例/反例/边界例）
- **置信度**：高/中/低，基于约束复杂度和输入歧义程度
- **风险点**：可能的问题或需要人工确认的地方

对 SKIPPED 的规则，明确列出需要补充的输入信息。

**总体评估：** 一段话总结整体质量和需要关注的点。

如果 RAG 动态样例区为空（RAG 不可用），阶段 4 必须提高风险提示级别：对所有非简单属性约束的规则，置信度至少降一级，并在风险点中标注「无 RAG 相似样例参考」。

如果发现明确错误，直接修正并在审查中标注修正内容。对不确定的问题，标为风险点交由人工判断。
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/prompt/fragments/05-stage-instructions.md
git commit -m "feat: add four-stage generation instructions (inv only)"
```

---

### Task 7: C++ 测试 harness 契约

**Files:**
- Create: `ocl-generation/prompt/fragments/06-cpp-test-template.md`

- [ ] **Step 1: 编写测试 harness 契约和边界测试标准**

Write to `ocl-generation/prompt/fragments/06-cpp-test-template.md`:

```markdown
## C++ 测试代码契约

生成测试代码时，严格遵循以下契约。

> **重要声明**：此模板是结构指引。`evaluate()` 函数签名、对象构造 API、断言宏等需根据项目实际测试框架调整。在统一 harness 从现有 100 个测试中抽取并固化之前，生成的测试代码视为「待适配骨架」，不宣称可直接编译执行。

### 统一契约

- 测试框架：Google Test（`TEST` / `ASSERT_TRUE` / `ASSERT_FALSE`）
- 约束求值入口：`evaluate(obj, "<constraint_name>") -> bool`
- 对象构造：`<ClassName> obj;` + `obj.set<Attr>(value);`
- 关联建立：`obj.add<Assoc>(relatedObj);`
- 头文件：`#include "<class_name>.h"` + `#include "ocl_evaluator.h"`

### 测试模板

```cpp
// ============================================================
// R<N>: <业务规则自然语言描述>
// OCL: context <Class> inv <name>: <expr>
// ============================================================

// 正例：构造满足约束的对象实例
TEST(<ContextClass>Test, <ConstraintName>_positive) {
    <ContextClass> obj;
    obj.set<Attr>(/* 满足约束的典型值，不要用边界值 */);
    // 如有关联对象：
    // <RelatedClass> related;
    // related.set<Attr>(/* 值 */);
    // obj.add<Assoc>(related);
    ASSERT_TRUE(evaluate(obj, "<constraint_name>"));
}

// 反例：构造违反约束的对象实例
TEST(<ContextClass>Test, <ConstraintName>_negative) {
    <ContextClass> obj;
    obj.set<Attr>(/* 明确违反约束的典型非法值 */);
    ASSERT_FALSE(evaluate(obj, "<constraint_name>"));
}

// 边界例（当约束含比较运算符或集合基数约束时必须生成）
TEST(<ContextClass>Test, <ConstraintName>_boundary) {
    <ContextClass> obj;
    obj.set<Attr>(/* 恰好在阈值上的值 */);
    ASSERT_<TRUE|FALSE>(evaluate(obj, "<constraint_name>"));
}
```

### 边界测试标准

当约束包含以下运算时，视为存在明确边界条件，必须生成边界例：

| 约束模式 | 边界值 | 边界例预期结果 | 反例值 |
|----------|--------|---------------|--------|
| `x > 0` | `0` | FALSE | `-1` |
| `x >= 0` | `0` | TRUE | `-1` |
| `x < 100` | `100` | FALSE | `101` |
| `x <= 100` | `100` | TRUE | `101` |
| `col->size() >= 1` | 1 个元素 | TRUE | 0 个元素 |
| `x = y` | `x == y` | TRUE | `x != y` |

### 测试数据设计原则

1. **正例**：选择明确满足约束的典型值，不要用边界值
2. **反例**：选择明确违反约束的典型非法值，让违反原因一目了然
3. **边界例**：选择约束条件的恰好临界值
4. **注释**：每个测试值旁标注计算过程或为什么满足/违反约束
5. **独立性**：每个 TEST 独立构造对象，不依赖其他测试的状态
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/prompt/fragments/06-cpp-test-template.md
git commit -m "feat: add C++ test harness contract with boundary test standards"
```

---

### Task 8: 输出格式约束

**Files:**
- Create: `ocl-generation/prompt/fragments/07-output-format.md`

- [ ] **Step 1: 编写输出格式约束**

Write to `ocl-generation/prompt/fragments/07-output-format.md`:

```markdown
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
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/prompt/fragments/07-output-format.md
git commit -m "feat: add output format constraints with XML stage tags"
```

---

### Task 9: Golden Examples 框架

**Files:**
- Create: `ocl-generation/prompt/examples/README.md`
- Create: `ocl-generation/prompt/examples/golden-01-attribute.md`
- Create: `ocl-generation/prompt/examples/golden-02-collection.md`
- Create: `ocl-generation/prompt/examples/golden-03-navigation.md`
- Create: `ocl-generation/prompt/examples/golden-04-enum-condition.md`
- Create: `ocl-generation/prompt/examples/golden-05-compound.md`

- [ ] **Step 1: 编写选取指南**

Write to `ocl-generation/prompt/examples/README.md`:

```markdown
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

完整四阶段输出，格式与 `prompt/fragments/07-output-format.md` 一致。
固定区样例的阶段 4 可精简为一行结论，不展开完整表格（节省 token）。

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
```

- [ ] **Step 2: 创建 5 个 golden example 模板文件**

每个文件结构相同。Write to `ocl-generation/prompt/examples/golden-01-attribute.md`:

```markdown
# Golden Example 1: 简单属性约束

> 模式：`context <Class> inv <name>: self.<attr> <op> <value>`
> 从 100 个样例中选取，需人工填充

<stage1>
## 模型结构

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|
<!-- 待从样例库选取填充 -->

## 关联关系

无

## 业务约束规则

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|
<!-- 待从样例库选取填充 -->

## 信息缺口

无信息缺口
</stage1>

<stage2>
<!-- 待从样例库选取填充：简单属性约束 OCL 代码 -->
</stage2>

<stage3>
<!-- 待从样例库选取填充：正例 + 反例 + 边界例测试代码 -->
</stage3>

<stage4>
<!-- 待填充：一行审查结论 -->
</stage4>
```

Write to `ocl-generation/prompt/examples/golden-02-collection.md`:

```markdown
# Golden Example 2: 集合量词约束

> 模式：`forAll` / `exists` / `select` 等集合量词操作
> 从 100 个样例中选取，需人工填充

<stage1>
## 模型结构

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|
<!-- 待从样例库选取填充 -->

## 关联关系

| 源类 | 目标类 | 关联名 | 多重性 | 说明 |
|------|--------|--------|--------|------|
<!-- 待从样例库选取填充 -->

## 业务约束规则

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|
<!-- 待从样例库选取填充 -->

## 信息缺口

无信息缺口
</stage1>

<stage2>
<!-- 待从样例库选取填充：集合量词约束 OCL 代码 -->
</stage2>

<stage3>
<!-- 待从样例库选取填充：正例 + 反例测试代码 -->
</stage3>

<stage4>
<!-- 待填充：一行审查结论 -->
</stage4>
```

Write to `ocl-generation/prompt/examples/golden-03-navigation.md`:

```markdown
# Golden Example 3: 关联导航约束

> 模式：跨对象引用，如 `self.<assoc>.<attr>` 或多级导航
> 从 100 个样例中选取，需人工填充

<stage1>
## 模型结构

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|
<!-- 待从样例库选取填充 -->

## 关联关系

| 源类 | 目标类 | 关联名 | 多重性 | 说明 |
|------|--------|--------|--------|------|
<!-- 待从样例库选取填充 -->

## 业务约束规则

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|
<!-- 待从样例库选取填充 -->

## 信息缺口

无信息缺口
</stage1>

<stage2>
<!-- 待从样例库选取填充：关联导航约束 OCL 代码 -->
</stage2>

<stage3>
<!-- 待从样例库选取填充：正例 + 反例测试代码 -->
</stage3>

<stage4>
<!-- 待填充：一行审查结论 -->
</stage4>
```

Write to `ocl-generation/prompt/examples/golden-04-enum-condition.md`:

```markdown
# Golden Example 4: 枚举状态条件约束

> 模式：`implies` / `if-then-else`，基于枚举值的条件分支
> 从 100 个样例中选取，需人工填充

<stage1>
## 模型结构

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|
<!-- 待从样例库选取填充 -->

## 关联关系

| 源类 | 目标类 | 关联名 | 多重性 | 说明 |
|------|--------|--------|--------|------|
<!-- 待从样例库选取填充（如有） -->

## 枚举类型

| 枚举名 | 值 |
|--------|-----|
<!-- 待从样例库选取填充 -->

## 业务约束规则

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|
<!-- 待从样例库选取填充 -->

## 信息缺口

无信息缺口
</stage1>

<stage2>
<!-- 待从样例库选取填充：implies/if-then-else 约束 OCL 代码 -->
</stage2>

<stage3>
<!-- 待从样例库选取填充：正例 + 反例测试代码 -->
</stage3>

<stage4>
<!-- 待填充：一行审查结论 -->
</stage4>
```

Write to `ocl-generation/prompt/examples/golden-05-compound.md`:

```markdown
# Golden Example 5: 复合聚合约束

> 模式：`collect` / `sum` / `let` 等聚合计算
> 从 100 个样例中选取，需人工填充

<stage1>
## 模型结构

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|
<!-- 待从样例库选取填充 -->

## 关联关系

| 源类 | 目标类 | 关联名 | 多重性 | 说明 |
|------|--------|--------|--------|------|
<!-- 待从样例库选取填充 -->

## 业务约束规则

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|
<!-- 待从样例库选取填充 -->

## 信息缺口

无信息缺口
</stage1>

<stage2>
<!-- 待从样例库选取填充：collect/sum/let 约束 OCL 代码 -->
</stage2>

<stage3>
<!-- 待从样例库选取填充：正例 + 反例 + 边界例测试代码 -->
</stage3>

<stage4>
<!-- 待填充：一行审查结论 -->
</stage4>
```

- [ ] **Step 3: 提交**

```bash
git add ocl-generation/prompt/examples/
git commit -m "feat: add golden examples framework with selection guide (v1 inv only)"
```

---

### Task 10: RAG 服务接口契约

**Files:**
- Create: `ocl-generation/rag-contract/openapi.yaml`

- [ ] **Step 1: 编写 OpenAPI 3.0 接口定义**

Write to `ocl-generation/rag-contract/openapi.yaml`:

```yaml
openapi: 3.0.3
info:
  title: OCL Example RAG Service
  description: |
    样例检索服务，输入业务描述文本和可选的结构摘要，返回最相似的 OCL inv 样例。
    独立仓库部署，本文件仅定义接口契约。
  version: 1.0.0

paths:
  /api/v1/search:
    post:
      summary: 检索相似样例
      description: 基于业务描述文本的语义相似度，返回最相关的 OCL inv 样例
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - query
              properties:
                query:
                  type: string
                  description: 业务描述文本
                  example: "订单系统中，订单总金额必须等于所有订单项金额之和"
                context_summary:
                  type: string
                  description: |
                    可选。UML 结构摘要，传入时用于提升检索相关性
                    （参与 rerank 阶段的结构相似度计算）。
                    不传时仅基于 query 做语义检索。
                  example: "Order(totalAmount: Real) --items[1..*]--> OrderItem(quantity: Integer, unitPrice: Real)"
                top_k:
                  type: integer
                  default: 2
                  minimum: 1
                  maximum: 10
                  description: 返回最相似的 K 个样例（默认 2，避免 token 失控）
                min_score:
                  type: number
                  format: float
                  default: 0.5
                  minimum: 0.0
                  maximum: 1.0
                  description: 最低相似度阈值
      responses:
        '200':
          description: 检索成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SearchResponse'
        '400':
          description: 请求参数错误
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: 服务内部错误
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/health:
    get:
      summary: 健康检查
      responses:
        '200':
          description: 服务正常
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "ok"
                  sample_count:
                    type: integer
                    description: 已索引的样例数量
                    example: 100

components:
  schemas:
    SearchResponse:
      type: object
      properties:
        results:
          type: array
          items:
            type: object
            required:
              - id
              - score
              - description
              - ocl
              - test_code
            properties:
              id:
                type: string
                description: 样例唯一标识
                example: "sample_042"
              score:
                type: number
                format: float
                description: 相似度分数 (0-1)
                example: 0.87
              description:
                type: string
                description: 原始业务描述文本
              context_summary:
                type: string
                description: UML 结构摘要（可选返回，用于改善样例拼装质量）
                example: "Order(totalAmount: Real) --items[1..*]--> OrderItem(quantity: Integer, unitPrice: Real)"
              pattern_tags:
                type: array
                items:
                  type: string
                description: 模式标签（可选返回，用于改善样例拼装质量）
                example: ["collection", "sum", "navigation"]
              ocl:
                type: string
                description: OCL 约束代码
              test_code:
                type: string
                description: C++ 测试代码
              stage1_ir:
                type: string
                description: 预生成的阶段 1 结构化理解（可选）

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          description: 错误类型
          example: "invalid_request"
        message:
          type: string
          description: 错误描述
          example: "query field is required"
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/rag-contract/openapi.yaml
git commit -m "feat: add RAG service OpenAPI contract with context_summary and error responses"
```

---

### Task 11: 组装完整 System Prompt

**Files:**
- Create: `ocl-generation/prompt/system-prompt.md`

- [ ] **Step 1: 组装完整 prompt**

Write to `ocl-generation/prompt/system-prompt.md`。组装规则：

1. 按 `fragments/01-*.md` 到 `fragments/07-*.md` 的编号顺序依次拼接内容
2. 各片段之间用 `---` 分隔线分隔
3. 保持片段的原始 Markdown 格式不变
4. 在末尾追加 Few-shot 样例区

完整文件结构：

```markdown
# OCL Generation System Prompt

<!-- 版本：prompt-v1.0 -->
<!-- 使用说明：将以下内容作为 system prompt 发送给大模型 -->
<!-- Few-shot 样例区的「RAG 动态区」需要在使用时动态填充 -->

---

[01-role-definition.md 的完整内容]

---

[02-ocl-syntax-reference.md 的完整内容]

---

[03-common-mistakes.md 的完整内容]

---

[04-input-contract.md 的完整内容]

---

[05-stage-instructions.md 的完整内容]

---

[06-cpp-test-template.md 的完整内容]

---

[07-output-format.md 的完整内容]

---

## Few-shot 样例

### 固定样例区 (Golden Examples)

<!-- 将 golden-01 到 golden-05 的完整四阶段内容依次粘贴到这里 -->
<!-- 当前为待填充状态，需完成 Golden Examples 选取后组装 -->

### RAG 动态样例区

<!-- 使用时，将 RAG 服务返回的样例填入此处 -->
<!-- 每个样例至少展示阶段 2（OCL）和阶段 3（测试），可附一行结构摘要 -->
<!-- 如果 RAG 不可用，此区留空，固定样例区保证基本生成质量 -->
<!-- 默认放置 1-2 个最相似样例 -->
```

组装时注意：
- 实际组装时用 `cat` 或脚本把 fragments 的内容直接内联，不保留 `[xxx 的完整内容]` 占位符
- Golden Examples 区需要等样例选取完成后才能最终填充
- RAG 动态区保留 HTML 注释占位，使用时动态替换

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/prompt/system-prompt.md
git commit -m "feat: assemble system prompt template (golden examples pending)"
```

---

### Task 12: 使用指南

**Files:**
- Create: `ocl-generation/docs/assembly-guide.md`

- [ ] **Step 1: 编写组装和使用指南**

Write to `ocl-generation/docs/assembly-guide.md`:

```markdown
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
```

- [ ] **Step 2: 提交**

```bash
git add ocl-generation/docs/assembly-guide.md
git commit -m "docs: add assembly and usage guide with version tracking"
```

---

### Task 13: 端到端验证

**Files:**
- Modify: `ocl-generation/prompt/system-prompt.md`（如发现问题）
- Modify: 任何需要修正的 fragments 文件

- [ ] **Step 1: 组装真实 system prompt**

将 `prompt/fragments/01-*.md` 到 `07-*.md` 的实际内容拼接到 `prompt/system-prompt.md` 中，替换占位引用。Golden Examples 区暂时留空（标注待填充）。

- [ ] **Step 2: 用合成样例测试 prompt**

使用以下合成业务描述作为测试输入：

```text
【类与属性】
- Employee(name: String, age: Integer, salary: Real)
- Department(name: String, budget: Real)

【关联】
- Employee.department -> Department [1]
- Department.employees -> Employee [1..*]

【业务规则】
- R1: 员工年龄必须在 18 到 65 之间
- R2: 员工薪资不能超过所在部门预算的 50%
- R3: 每个部门至少有一名员工
```

- [ ] **Step 3: 将 system prompt + 测试输入发送给大模型**

验证检查清单：
- [ ] 输出是否包含四个阶段的 `<stage1>` 到 `<stage4>` XML 标签？
- [ ] 阶段 1 是否正确提取了 Employee 和 Department 的所有属性？
- [ ] 阶段 1 的 R1 涉及属性是否列出了 age？R2 是否列出了 salary、department、budget？
- [ ] 阶段 2 是否生成了 3 条 `inv` 约束（不是 pre/post）？
- [ ] 阶段 2 是否只使用了阶段 1 列出的元素（不臆造）？
- [ ] 阶段 3 是否为 R1（含 `>=`/`<=`）生成了边界例？
- [ ] 阶段 3 的边界例值是否正确（如 `age = 18` 为 TRUE，`age = 17` 为反例）？
- [ ] 阶段 4 是否包含审查表格和置信度？
- [ ] 阶段 4 是否声明了自我审查的局限性？

- [ ] **Step 4: 修复发现的问题**

如果验证发现 prompt 有问题（指令不清晰、输出格式不对、模型跳过阶段等），修改对应的 `prompt/fragments/` 文件并重新组装 `system-prompt.md`。

- [ ] **Step 5: 提交最终版本**

```bash
git add ocl-generation/
git commit -m "feat: complete OCL generation prompt template v1.0 (golden examples pending)"
```

更新 `VERSION` 文件：

```text
prompt-v1.0
golden-v0 (pending selection from 100 samples)
index-v0 (pending RAG deployment)
harness-v0 (pending extraction from existing tests)
```
