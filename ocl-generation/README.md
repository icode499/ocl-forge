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
