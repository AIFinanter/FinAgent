"""
初始化合规知识库 — 加载监管条文到 ChromaDB 向量数据库
"""

import sys
import os

# 添加项目根目录到 path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config
from knowledge_base.rag_engine import ComplianceRAG


def main():
    print("=" * 60)
    print("FinGuard — 合规知识库初始化")
    print("=" * 60)

    # 确保目录存在
    os.makedirs(config.rag.persist_dir, exist_ok=True)

    # 初始化 RAG 引擎
    rag = ComplianceRAG(
        persist_dir=config.rag.persist_dir,
        model_name=config.rag.embedding_model
    )

    # 加载监管条文
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "knowledge_base",
        "regulations",
        "finance_regulations.json"
    )

    print(f"\n📂 条文文件: {json_path}")
    count = rag.load_regulations(json_path)
    print(f"✅ 已加载 {count} 条监管条文")

    # 验证检索
    print("\n🔍 验证检索: '数据跨境传输'")
    results = rag.retrieve("数据跨境传输")

    for i, r in enumerate(results, 1):
        print(f"\n  #{i} (距离: {r['distance']:.4f})")
        print(f"     {r['document'][:80]}...")
        print(f"     处罚: {r['metadata'].get('penalty', '无')}")

    print("\n" + "=" * 60)
    print("✅ 知识库初始化完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
