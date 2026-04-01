## OCL 2.4 语法规范速查

> v1 只生成 `inv` 约束。其他约束类型（pre/post/body/def/init）列出仅供参考，不要在输出中使用。

### 约束类型

- **`context <Class> inv <name>: <expr>`** — 不变量，任何时刻都必须为 true **（v1 唯一输出类型）**
- `context <Class>::<op>(<params>) pre <name>: <expr>` — 前置条件（v1 不支持）
- `context <Class>::<op>(<params>) post <name>: <expr>` — 后置条件（v1 不支持）
- `context <Class>::<op>(<params>): <Type> body <name>: <expr>` — 操作体定义（v1 不支持）
- `def` — 辅助定义（v1 不支持；本速查不提供语法模板，避免误导）
- `init` — 初始值（v1 不支持；本速查不提供语法模板，避免误导）

### 基本表达式

- `self` — 当前上下文对象
- `self.<attr>` — 访问属性
- `self.<assoc>` — 导航关联（返回集合或单个对象，取决于多重性）
- `self.<op>(<args>)` — 调用操作（v1 输入契约默认不包含操作级约束，除非用户输入明确给出且规则明确允许）

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
