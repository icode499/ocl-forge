# OCL 代码生成系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个轻量化的 prompt template，引导大模型按四阶段流程生成 OCL 约束代码和 C++ 测试代码，配合独立的 RAG 样例检索服务接口契约。

**Architecture:** 核心是一个多阶段 prompt template（结构化理解 → OCL 生成 → 测试生成 → 自我审查），配合固定 + RAG 动态的 few-shot 样例区。RAG 服务独立仓库，仅定义接口契约。

**Tech Stack:** Prompt engineering（纯文本），OpenAPI 3.0（RAG 接口契约），Markdown

---

## 文件结构

```
ocl-generation/
├── prompt/
│   ├── system-prompt.md              # 完整的 system prompt 模板（最终交付物）
│   ├── fragments/                    # prompt 的各个组成片段
│   │   ├── role-definition.md        # 角色定义
│   │   ├── ocl-syntax-reference.md   # OCL 2.4 语法速查
│   │   ├── common-mistakes.md        # 常见易错点清单
│   │   ├── stage-instructions.md     # 四阶段生成指令
│   │   ├── cpp-test-template.md      # C++ 测试模板骨架
│   │   └── output-format.md          # 输出格式约束
│   └── examples/
│       ├── README.md                 # Golden Examples 选取指南
│       ├── golden-01-attribute.md    # 固定样例：简单属性约束
│       ├── golden-02-collection.md   # 固定样例：集合操作约束
│       ├── golden-03-navigation.md   # 固定样例：关联导航约束
│       ├── golden-04-pre-post.md     # 固定样例：前置/后置条件
│       └── golden-05-compound.md     # 固定样例：复合约束
├── rag-contract/
│   └── openapi.yaml                  # RAG 服务 OpenAPI 3.0 接口定义
├── docs/
│   └── assembly-guide.md             # Prompt 组装和使用指南
└── README.md                         # 项目说明
```

说明：
- `prompt/fragments/` 存放 prompt 的各个独立片段，方便单独维护和迭代
- `prompt/system-prompt.md` 是最终组装好的完整 prompt，直接可用
- `prompt/examples/golden-*.md` 需要用户从 100 个样例中选取填充（Task 7 提供选取指南和模板）
- `rag-contract/` 定义 RAG 服务的接口契约，供独立仓库实现

---

### Task 1: 项目脚手架

**Files:**
- Create: `README.md`
- Create: `prompt/fragments/` (directory)
- Create: `prompt/examples/` (directory)
- Create: `rag-contract/` (directory)
- Create: `docs/` (directory)

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p prompt/fragments prompt/examples rag-contract docs
```

- [ ] **Step 2: 创建项目 README**

```markdown
# OCL Generation Prompt Template

利用大模型生成 OMG OCL 约束代码和 C++ 业务测试代码的 prompt template。

## 项目结构

- `prompt/system-prompt.md` — 完整的 system prompt，直接可用
- `prompt/fragments/` — prompt 各片段，独立维护
- `prompt/examples/` — Few-shot golden examples
- `rag-contract/` — RAG 样例检索服务接口定义
- `docs/` — 使用指南

## 快速开始

参见 `docs/assembly-guide.md`
```

- [ ] **Step 3: 初始化 git 仓库并提交**

```bash
git init
git add README.md
git commit -m "chore: init project structure"
```

---

### Task 2: OCL 语法规范速查

**Files:**
- Create: `prompt/fragments/ocl-syntax-reference.md`

- [ ] **Step 1: 编写 OCL 2.4 核心语法速查**

```markdown
## OCL 2.4 语法规范速查

### 约束类型

- `context <Class> inv <name>: <expr>` — 不变量，任何时刻都必须为 true
- `context <Class>::<op>(<params>) pre <name>: <expr>` — 前置条件
- `context <Class>::<op>(<params>) post <name>: <expr>` — 后置条件
- `context <Class>::<op>(<params>): <Type> body <name>: <expr>` — 操作体定义
- `context <Class> def <name>: <Type> = <expr>` — 辅助定义
- `context <Class> init <name>: <expr>` — 初始值

### 基本表达式

- `self` — 当前上下文对象
- `self.<attr>` — 访问属性
- `self.<assoc>` — 导航关联（返回集合或单个对象）
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
context Order inv:
  let total: Real = self.items->collect(i | i.price)->sum() in
  total > 0 and total <= self.maxAmount
```

### @pre 表达式（后置条件中使用）

```ocl
context Account::withdraw(amount: Real) post:
  self.balance = self.balance@pre - amount
```
```

- [ ] **Step 2: 验证语法覆盖度**

检查清单：
- 是否覆盖了所有约束类型（inv/pre/post/body/def/init）
- 是否覆盖了所有集合操作
- 是否包含 let 和 @pre 等高级特性
- 是否包含类型操作

- [ ] **Step 3: 提交**

```bash
git add prompt/fragments/ocl-syntax-reference.md
git commit -m "feat: add OCL 2.4 syntax quick reference"
```

---

### Task 3: 常见易错点清单

**Files:**
- Create: `prompt/fragments/common-mistakes.md`

- [ ] **Step 1: 编写常见易错点**

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

3. **forAll/exists 的变量绑定**
   - 错误：`self.items->forAll(quantity > 0)`
   - 正确：`self.items->forAll(i | i.quantity > 0)`

4. **collect 后的集合类型变化**
   - `Set->collect()` 返回 `Bag`，不是 `Set`
   - 如需去重，追加 `->asSet()`

5. **substring 是 1-based**
   - 错误：`s.substring(0, 3)`
   - 正确：`s.substring(1, 3)`

### 业务逻辑层面

6. **臆造不存在的属性或关联**
   - 必须严格使用模型中定义的类名、属性名、关联名
   - 不得假设模型中未声明的元素

7. **多重性混淆**
   - 多重性为 `0..1` 的关联导航结果可能为 null，需要处理
   - 多重性为 `*` 的关联导航结果是集合，不能当单个对象用

8. **忽略继承关系**
   - 子类继承父类的所有约束
   - 在子类上下文中可以访问父类属性

9. **implies 的短路语义**
   - `a implies b`：当 a 为 false 时整个表达式为 true
   - 常用于条件约束：`self.status = #active implies self.balance >= 0`

10. **集合操作链的空集处理**
    - `emptySet->forAll(...)` 返回 true（空集上的全称量词为真）
    - `emptySet->exists(...)` 返回 false
    - 如果业务上空集不合法，需要额外加 `->notEmpty()` 检查
```

- [ ] **Step 2: 提交**

```bash
git add prompt/fragments/common-mistakes.md
git commit -m "feat: add common OCL generation mistakes guide"
```

---

### Task 4: C++ 测试模板骨架

**Files:**
- Create: `prompt/fragments/cpp-test-template.md`

- [ ] **Step 1: 编写测试模板**

```markdown
## C++ 测试代码模板

生成测试代码时，严格遵循以下模板结构。

### 模板骨架

对每条 OCL 约束，生成三类测试：

```cpp
// ============================================================
// R<N>: <业务规则自然语言描述>
// OCL: <对应的 OCL 约束表达式>
// ============================================================

// 正例：构造满足约束的对象实例
TEST(<ContextClass>Test, <ConstraintName>_positive) {
    // 1. 构造对象并设置属性
    <ContextClass> obj;
    obj.set<Attr>(/* 满足约束的值 */);

    // 2. 如有关联对象，构造并关联
    // <RelatedClass> related;
    // related.set<Attr>(/* 值 */);
    // obj.add<Assoc>(related);

    // 3. 断言约束通过
    ASSERT_TRUE(evaluate(obj, "<constraint_name>"));
}

// 反例：构造违反约束的对象实例
TEST(<ContextClass>Test, <ConstraintName>_negative) {
    <ContextClass> obj;
    obj.set<Attr>(/* 违反约束的值 */);
    ASSERT_FALSE(evaluate(obj, "<constraint_name>"));
}

// 边界例：构造处于约束边界的对象实例
TEST(<ContextClass>Test, <ConstraintName>_boundary) {
    <ContextClass> obj;
    obj.set<Attr>(/* 边界值 */);
    ASSERT_<TRUE|FALSE>(evaluate(obj, "<constraint_name>"));
}
```

### 测试数据设计原则

1. **正例**：选择明确满足约束的典型值，不要用边界值
2. **反例**：选择明确违反约束的值，让违反原因一目了然
3. **边界例**：选择约束条件的临界值（如 `>= 0` 的边界是 `0` 和 `-1`）
4. **注释**：每个测试值旁标注为什么这个值满足/违反约束
5. **独立性**：每个 TEST 独立构造对象，不依赖其他测试的状态

### 重要说明

- `evaluate()` 函数签名、对象构造方式、断言宏等需根据项目实际测试框架调整
- 此模板为结构指引，具体 API 以项目现有测试代码为准
- 生成测试时，必须使用阶段 1 提取的类名和属性名，不得臆造
```

- [ ] **Step 2: 提交**

```bash
git add prompt/fragments/cpp-test-template.md
git commit -m "feat: add C++ test template skeleton"
```

---

### Task 5: 角色定义与输出格式

**Files:**
- Create: `prompt/fragments/role-definition.md`
- Create: `prompt/fragments/output-format.md`

- [ ] **Step 1: 编写角色定义**

```markdown
## 角色定义

你是一个 OCL（Object Constraint Language）代码生成专家，精通 OMG OCL 2.4 规范。

你的职责是：
1. 理解用户提供的业务描述文本（包含 UML 模型信息和业务约束需求）
2. 按照四个阶段逐步输出：结构化理解 → OCL 代码 → C++ 测试代码 → 自我审查
3. 确保生成的 OCL 严格符合语法规范，且准确表达业务语义
4. 确保生成的测试代码能有效验证 OCL 约束的正确性

关键原则：
- 先理解，再生成。不要跳过结构化理解阶段直接写 OCL
- 只使用模型中定义的元素（类、属性、关联），不得臆造
- 每条 OCL 约束必须标注对应的业务规则编号，保持可追溯性
- 测试必须包含正例和反例，边界例视情况添加
```

- [ ] **Step 2: 编写输出格式约束**

```markdown
## 输出格式

严格按以下 XML 标签分隔四个阶段的输出：

<stage1>
阶段 1：结构化理解
- 模型结构表格（类、属性、类型、说明）
- 关联关系表格（源类、目标类、关联名、多重性）
- 枚举类型（如有）
- 业务约束规则列表（编号 R1/R2/...、约束类型、上下文类、自然语言描述）
</stage1>

<stage2>
阶段 2：OCL 代码
- 每条约束前用注释标注规则编号和自然语言描述
- OCL 代码遵循 OMG OCL 2.4 语法
</stage2>

<stage3>
阶段 3：C++ 测试代码
- 每条约束对应一组测试（正例 + 反例 + 边界例）
- 遵循 C++ 测试模板结构
</stage3>

<stage4>
阶段 4：自我审查
- 审查结果表格（规则、OCL 语法、业务逻辑、测试覆盖、置信度、风险点）
- 总体评估
</stage4>
```

- [ ] **Step 3: 提交**

```bash
git add prompt/fragments/role-definition.md prompt/fragments/output-format.md
git commit -m "feat: add role definition and output format constraints"
```

---

### Task 6: 四阶段生成指令

**Files:**
- Create: `prompt/fragments/stage-instructions.md`

- [ ] **Step 1: 编写四阶段指令**

```markdown
## 四阶段生成指令

收到用户的业务描述文本后，严格按以下四个阶段依次输出。每个阶段的输出是下一个阶段的输入，不得跳过任何阶段。

---

### 阶段 1：结构化理解

从用户输入中提取以下信息，以 markdown 表格呈现：

**1.1 模型结构**

提取所有类及其属性：

| 类名 | 属性 | 类型 | 说明 |
|------|------|------|------|

**1.2 关联关系**

提取类之间的关联：

| 源类 | 目标类 | 关联名 | 多重性 | 说明 |
|------|--------|--------|--------|------|

**1.3 枚举类型**（如有）

| 枚举名 | 值 |
|--------|-----|

**1.4 业务约束规则**

将业务约束拆解为编号规则：

| 编号 | 约束类型 | 上下文类 | 涉及属性/关联 | 自然语言描述 |
|------|----------|----------|---------------|-------------|

规则编号格式：R1, R2, R3...
约束类型：inv（不变量）、pre（前置条件）、post（后置条件）

**检查点：** 输出阶段 1 后，自问：
- 是否遗漏了输入文本中提到的任何类、属性或关联？
- 每条业务规则是否只表达了一个约束？复合约束是否已拆分？
- 约束类型标注是否正确？

---

### 阶段 2：OCL 生成

基于阶段 1 的结构化理解，逐条将业务规则翻译为 OCL：

**规则：**
1. 每条 OCL 前用注释标注规则编号和自然语言描述：`-- R<N>: <描述>`
2. 必须使用阶段 1 提取的类名、属性名、关联名，不得臆造
3. 为每条约束命名（`inv <name>:`），名称应有业务含义
4. 遵循 OCL 语法规范速查中的语法规则
5. 避免常见易错点清单中列出的错误

**检查点：** 输出阶段 2 后，自问：
- 每条 OCL 是否都有对应的规则编号？
- 是否使用了模型中不存在的属性或关联？
- 集合操作是否使用了 `->` 而非 `.`？
- `forAll`/`exists` 是否正确绑定了迭代变量？

---

### 阶段 3：C++ 测试生成

基于阶段 1 的模型结构和阶段 2 的 OCL 代码，为每条约束生成测试：

**规则：**
1. 每条约束至少生成正例（positive）和反例（negative）两个测试
2. 对有明确边界条件的约束（如 `>= 0`、`<= maxValue`），额外生成边界例（boundary）
3. 遵循 C++ 测试模板的结构
4. 测试数据必须使用阶段 1 中的类和属性
5. 每个测试值旁用注释说明为什么满足/违反约束

**检查点：** 输出阶段 3 后，自问：
- 每条 OCL 约束是否都有对应的测试？
- 正例的测试数据是否确实满足约束？
- 反例的测试数据是否确实违反约束？
- 是否使用了阶段 1 中不存在的类或属性？

---

### 阶段 4：自我审查

对阶段 2 和阶段 3 的输出进行系统性审查：

**审查项目：**

| 规则 | OCL 语法 | 业务逻辑 | 测试覆盖 | 置信度 | 风险点 |
|------|----------|----------|----------|--------|--------|

- **OCL 语法**：是否符合 OCL 2.4 规范，无语法错误
- **业务逻辑**：OCL 是否准确表达了对应的业务规则 R<N>
- **测试覆盖**：是否有正例+反例，边界例是否需要但缺失
- **置信度**：高/中/低，基于约束复杂度和歧义程度
- **风险点**：可能的问题或需要人工确认的地方

**总体评估：** 一段话总结整体质量和需要关注的点。

如果发现问题，直接在审查中修正 OCL 或测试代码，并标注修正内容。
```

- [ ] **Step 2: 提交**

```bash
git add prompt/fragments/stage-instructions.md
git commit -m "feat: add four-stage generation instructions"
```

---

### Task 7: Golden Examples 框架与选取指南

**Files:**
- Create: `prompt/examples/README.md`
- Create: `prompt/examples/golden-01-attribute.md`
- Create: `prompt/examples/golden-02-collection.md`
- Create: `prompt/examples/golden-03-navigation.md`
- Create: `prompt/examples/golden-04-pre-post.md`
- Create: `prompt/examples/golden-05-compound.md`

- [ ] **Step 1: 编写 Golden Examples 选取指南**

```markdown
# Golden Examples 选取指南

## 目的

从现有 100 个样例中精选 5 个，覆盖最常见的 OCL 模式，作为 prompt 的固定 few-shot 样例。

## 五个类别

| 类别 | 文件 | OCL 模式 | 选取标准 |
|------|------|----------|----------|
| 1 | golden-01-attribute.md | 简单属性约束 | `inv: self.<attr> <op> <value>` 形式 |
| 2 | golden-02-collection.md | 集合操作约束 | 使用 select/forAll/exists/collect 等 |
| 3 | golden-03-navigation.md | 关联导航约束 | 跨对象引用，涉及关联导航 |
| 4 | golden-04-pre-post.md | 前置/后置条件 | 使用 pre/post，涉及操作约束 |
| 5 | golden-05-compound.md | 复合约束 | 多条件组合，使用 implies/if-then/let |

## 选取标准

1. **代表性**：该类别中最典型的用法
2. **复杂度适中**：不要太简单（没有学习价值），不要太复杂（占用过多 token）
3. **业务语义清晰**：业务描述和 OCL 之间的对应关系一目了然
4. **测试完整**：有正例和反例，最好有边界例

## 样例格式

每个 golden example 文件必须包含完整的四阶段输出。参见各文件中的模板。

## 操作步骤

1. 对 100 个样例的 OCL 代码做模式分类，归入上述 5 个类别
2. 每个类别中，按选取标准排序，选出排名第一的样例
3. 为选出的样例补充完整的四阶段输出（如果原始样例没有阶段 1 和阶段 4）
4. 填入对应的 golden-*.md 文件
```

- [ ] **Step 2: 创建 5 个 golden example 模板文件**

每个文件结构相同，以 `golden-01-attribute.md` 为例：

```markdown
# Golden Example 1: 简单属性约束

> 从 100 个样例中选取，覆盖 `inv: self.<attr> <op> <value>` 模式

## 输入：业务描述

<!-- 将选取的样例的业务描述文本粘贴到这里 -->

```text
[待填充：业务描述文本，包含 UML 模型信息和约束需求]
```

## 阶段 1：结构化理解

<!-- 基于业务描述提取的结构化信息 -->

```
[待填充：模型结构表格 + 关联关系表格 + 业务约束规则列表]
```

## 阶段 2：OCL 代码

<!-- 该样例的 OCL 约束代码 -->

```ocl
[待填充：OCL 代码，每条前标注规则编号]
```

## 阶段 3：C++ 测试代码

<!-- 该样例的测试代码 -->

```cpp
[待填充：正例 + 反例 + 边界例测试代码]
```

## 阶段 4：审查结果

<!-- 简要审查结论 -->

```
[待填充：审查结果表格，可精简为一行结论]
```
```

对 `golden-02-collection.md` 到 `golden-05-compound.md` 重复相同结构，仅修改标题和模式描述：
- `golden-02-collection.md`: "Golden Example 2: 集合操作约束"，覆盖 `select/forAll/exists/collect` 模式
- `golden-03-navigation.md`: "Golden Example 3: 关联导航约束"，覆盖跨对象引用模式
- `golden-04-pre-post.md`: "Golden Example 4: 前置/后置条件"，覆盖 `pre/post` 模式
- `golden-05-compound.md`: "Golden Example 5: 复合约束"，覆盖 `implies/if-then/let` 模式

- [ ] **Step 3: 提交**

```bash
git add prompt/examples/
git commit -m "feat: add golden examples framework and selection guide"
```

---

### Task 8: RAG 服务接口契约

**Files:**
- Create: `rag-contract/openapi.yaml`

- [ ] **Step 1: 编写 OpenAPI 3.0 接口定义**

```yaml
openapi: 3.0.3
info:
  title: OCL Example RAG Service
  description: 样例检索服务，输入业务描述文本，返回最相似的 OCL 样例
  version: 1.0.0

paths:
  /api/v1/search:
    post:
      summary: 检索相似样例
      description: 基于业务描述文本的语义相似度，返回最相关的 OCL 样例
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
                top_k:
                  type: integer
                  default: 3
                  minimum: 1
                  maximum: 10
                  description: 返回最相似的 K 个样例
                min_score:
                  type: number
                  format: float
                  default: 0.0
                  minimum: 0.0
                  maximum: 1.0
                  description: 最低相似度阈值
      responses:
        '200':
          description: 检索成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  results:
                    type: array
                    items:
                      type: object
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
                        ocl:
                          type: string
                          description: OCL 约束代码
                        test_code:
                          type: string
                          description: C++ 测试代码
                        stage1_ir:
                          type: string
                          description: 预生成的阶段1结构化理解（可选）
        '400':
          description: 请求参数错误
        '500':
          description: 服务内部错误

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
```

- [ ] **Step 2: 提交**

```bash
git add rag-contract/openapi.yaml
git commit -m "feat: add RAG service OpenAPI contract"
```

---

### Task 9: 组装完整 System Prompt

**Files:**
- Create: `prompt/system-prompt.md`

- [ ] **Step 1: 组装完整 prompt**

将 `prompt/fragments/` 下的所有片段按以下顺序组装为一个完整的 system prompt 文件：

```markdown
# OCL Generation System Prompt

<!-- 使用说明：将以下内容作为 system prompt 发送给大模型 -->
<!-- Few-shot 样例区的 [RAG 动态区] 需要在使用时动态填充 -->

---

[粘贴 role-definition.md 的内容]

---

[粘贴 ocl-syntax-reference.md 的内容]

---

[粘贴 common-mistakes.md 的内容]

---

[粘贴 stage-instructions.md 的内容]

---

[粘贴 cpp-test-template.md 的内容]

---

[粘贴 output-format.md 的内容]

---

## Few-shot 样例

### 固定样例区 (Golden Examples)

[粘贴 golden-01 到 golden-05 的完整四阶段内容]

### RAG 动态样例区

<!-- 使用时，将 RAG 服务返回的样例填入此处 -->
<!-- 每个样例展示阶段 2（OCL）和阶段 3（测试）即可，节省 token -->
<!-- 如果 RAG 不可用，此区留空 -->
```

组装时注意：
- 各片段之间用分隔线分隔
- 保持片段的原始格式，不要修改内容
- Golden Examples 区需要等 Task 7 的样例填充完成后才能最终组装
- RAG 动态区保留占位符，使用时动态替换

- [ ] **Step 2: 提交**

```bash
git add prompt/system-prompt.md
git commit -m "feat: assemble complete system prompt template"
```

---

### Task 10: 使用指南

**Files:**
- Create: `docs/assembly-guide.md`

- [ ] **Step 1: 编写组装和使用指南**

内容覆盖：

1. **快速开始**：三种使用方式（无 RAG 直接用 / 配合 RAG / 手动选样例）
2. **输入格式**：业务描述文本应包含什么（UML 模型信息 + 约束需求），附示例
3. **输出说明**：四个阶段 XML 标签的含义
4. **审查建议**：先看 stage1 → 再看 stage4 → 最后看 stage2/stage3
5. **Token 预算**：遇到上下文长度限制时的缩减策略
6. **维护**：如何新增样例、更新 golden examples、补充易错点

输入示例：

```text
系统中有 Order（订单）和 OrderItem（订单项）两个类。
Order 有属性 totalAmount（Real 类型）和 status（OrderStatus 枚举）。
OrderItem 有属性 quantity（Integer 类型）和 unitPrice（Real 类型）。
Order 与 OrderItem 是一对多关联（关联名 items）。

业务约束：
1. 订单总金额必须等于所有订单项金额之和
2. 每个订单项的数量必须大于 0
3. 订单状态为 active 时，总金额必须大于 0
```

RAG 调用示例：

```bash
curl -X POST http://<rag-service>/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "你的业务描述文本", "top_k": 3}'
```

- [ ] **Step 2: 提交**

```bash
git add docs/assembly-guide.md
git commit -m "docs: add assembly and usage guide"
```

---

### Task 11: 端到端验证

**Files:**
- Modify: `prompt/system-prompt.md`（如发现问题）

- [ ] **Step 1: 用合成样例测试 prompt**

使用以下合成业务描述作为测试输入：

```text
系统中有 Employee（员工）和 Department（部门）两个类。
Employee 有属性 name（String）、age（Integer）、salary（Real）。
Department 有属性 name（String）、budget（Real）。
Employee 与 Department 是多对一关联（关联名 department）。
Department 与 Employee 是一对多关联（关联名 employees）。

业务约束：
1. 员工年龄必须在 18 到 65 之间
2. 员工薪资不能超过所在部门预算的 50%
3. 每个部门至少有一名员工
```

- [ ] **Step 2: 将 system prompt 内容和测试输入发送给大模型**

验证检查清单：
- [ ] 输出是否包含四个阶段的 XML 标签？
- [ ] 阶段 1 是否正确提取了 Employee、Department 及其属性和关联？
- [ ] 阶段 2 是否生成了 3 条 OCL 约束，分别标注 R1/R2/R3？
- [ ] 阶段 2 的 OCL 语法是否正确？
- [ ] 阶段 3 是否为每条约束生成了正例和反例？
- [ ] 阶段 4 是否给出了审查表格？

- [ ] **Step 3: 修复发现的问题**

如果验证发现 prompt 有问题（如指令不清晰导致模型跳过某个阶段、输出格式不对等），修改对应的 `prompt/fragments/` 文件并重新组装 `system-prompt.md`。

- [ ] **Step 4: 提交最终版本**

```bash
git add -A
git commit -m "feat: complete OCL generation prompt template v1.0"
```
