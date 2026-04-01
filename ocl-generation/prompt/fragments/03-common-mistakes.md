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

6. **inv 命名是项目可追溯性约定（非 OCL 语法硬性要求）**
   - 建议：`context Order inv positiveTotal: self.total > 0`
   - 目的：便于将约束映射到业务规则编号（R1, R2...）

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
   - 常用于条件约束：`self.status = Status::active implies self.balance >= 0`
   - 注意：这意味着 status 不是 active 的对象总是满足该约束

10. **集合操作链的空集处理**
    - `emptySet->forAll(...)` 返回 true（空集上的全称量词为真）
    - `emptySet->exists(...)` 返回 false
    - 如果业务上空集不合法，需要额外加 `->notEmpty()` 检查
    - 示例：`self.items->notEmpty() and self.items->forAll(i | i.quantity > 0)`
