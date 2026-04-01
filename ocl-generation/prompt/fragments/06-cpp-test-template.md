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
