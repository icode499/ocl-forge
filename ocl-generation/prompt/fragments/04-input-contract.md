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
