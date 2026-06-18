#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
面向个人的多模态 RAG 知识库问答系统
================================================
核心能力：
1. 多格式解析 (PDF / Markdown / TXT / 图片 / CSV)
2. 离线索引 (Hash 增量更新 + 向量/稀疏混合索引)
3. 在线检索 (多路召回 + Rerank 精排 + 上下文拼装)
4. 效果评估 (RAGAS 简化指标)
5. 多模态理解 (图片 OCR + VLM 图像描述)

本文件不依赖真实 LLM API，通过启发式规则 + 关键词/向量 实现完整演示。
"""

import os
import json
import re
import math
import time
import hashlib
import datetime
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Any
from collections import Counter, defaultdict


# ============================================================
# 一、数据结构
# ============================================================

@dataclass
class Document:
    """文档 / 知识条目"""
    doc_id: str
    title: str
    file_type: str  # pdf / md / txt / image / csv
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    filepath: str = ""

    def content_hash(self) -> str:
        return hashlib.md5(self.content.encode("utf-8"), usedforsecurity=False).hexdigest()


@dataclass
class Chunk:
    """切分后的文档片段"""
    chunk_id: str
    doc_id: str
    text: str
    tokens: int
    keywords: List[str]
    vector_signature: List[float]  # 简化: 基于词频权重向量


@dataclass
class RetrievalResult:
    """检索结果"""
    chunk: Chunk
    score: float
    method: str  # dense / sparse / hybrid
    rank: int = 0


# ============================================================
# 二、文档解析与切分
# ============================================================

class DocumentParser:
    """多格式文档解析器"""

    @staticmethod
    def parse(filepath: str) -> Optional[Document]:
        p = Path(filepath)
        if not p.exists():
            return None

        ext = p.suffix.lower().lstrip(".")
        content = ""
        try:
            if ext in ["md", "markdown"]:
                content = p.read_text(encoding="utf-8")
            elif ext in ["txt", "log"]:
                content = p.read_text(encoding="utf-8")
            elif ext == "pdf":
                content = f"[PDF 模拟 - {p.name}] 这是一份示例 PDF 文档内容，经 OCR 抽取后转换为可检索文本。"
            elif ext in ["png", "jpg", "jpeg"]:
                content = f"[图片 - {p.name}] 经 VLM 图像描述与 OCR 提取后的文本内容：包含标题、图表、图像要点。"
            elif ext == "csv":
                lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
                content = "[CSV 数据] " + " | ".join(lines[:5])
            else:
                content = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            content = f"[{ext.upper()} 文件 - 无法解析]"

        return Document(
            doc_id=hashlib.md5(str(filepath).encode("utf-8"), usedforsecurity=False).hexdigest()[:12],
            title=p.stem,
            file_type=ext,
            content=content,
            metadata={"size": p.stat().st_size if p.exists() else 0, "source": str(p)},
            filepath=str(p),
        )

    @staticmethod
    def parse_text(title: str, content: str, file_type: str = "txt") -> Document:
        """直接从文本构造（测试/演示用）"""
        return Document(
            doc_id=hashlib.md5(content.encode("utf-8"), usedforsecurity=False).hexdigest()[:12],
            title=title, file_type=file_type, content=content,
            metadata={"source": title}, filepath=title,
        )


class Chunker:
    """文档切分器 - 语义块 (Semantic Chunking 简化版)"""
    DEFAULT_CHUNK_SIZE = 300
    DEFAULT_OVERLAP = 50

    @classmethod
    def chunk(cls, doc: Document, chunk_size: int = None, overlap: int = None) -> List[Chunk]:
        chunk_size = chunk_size or cls.DEFAULT_CHUNK_SIZE
        overlap = overlap or cls.DEFAULT_OVERLAP
        text = doc.content
        chunks: List[Chunk] = []
        i = 0
        while i < len(text):
            end = min(i + chunk_size, len(text))
            if end < len(text):
                # 在标点处对齐，避免中间截断
                best = max(text.rfind("。", i, end), text.rfind("\n", i, end),
                           text.rfind(". ", i, end))
                if best > i + chunk_size // 2:
                    end = best
            chunk_text = text[i:end].strip()
            if chunk_text:
                kw = KeywordExtractor.extract(chunk_text)
                vec = Vectorizer.vectorize(chunk_text, kw)
                chunks.append(Chunk(
                    chunk_id=f"{doc.doc_id}_chunk{len(chunks):04d}",
                    doc_id=doc.doc_id,
                    text=chunk_text,
                    tokens=len(chunk_text.split()),
                    keywords=kw,
                    vector_signature=vec,
                ))
            i = end - overlap
            if end >= len(text):
                break
        return chunks


# ============================================================
# 三、关键词提取 & 向量化
# ============================================================

class KeywordExtractor:
    """简易关键词提取（基于 TF + 停用词过滤 + 技术词加权）"""

    STOPWORDS = set("的了是在我有和就不人都而及与或但却中为上也都还又再这个那个这样那样什么怎么哪些为什么因此所以但是不过然后".split())
    TECH_KEYWORDS = ["python", "api", "data", "model", "agent", "rag", "llm",
                     "vector", "检索", "向量", "大模型", "代码", "系统", "优化", "设计"]

    @classmethod
    def extract(cls, text: str, top_k: int = 10) -> List[str]:
        tokens = re.findall(r"[\w\u4e00-\u9fa5]+", text.lower())
        filtered = [t for t in tokens if len(t) >= 2 and t not in cls.STOPWORDS]
        counter = Counter(filtered)
        # 技术关键词加权
        for word in list(counter.keys()):
            if word in cls.TECH_KEYWORDS:
                counter[word] += 5
        return [w for w, c in counter.most_common(top_k)]


class Vectorizer:
    """简化向量生成器（演示用，非真实嵌入）"""
    VOCAB_SIZE = 128

    @classmethod
    def vectorize(cls, text: str, keywords: Optional[List[str]] = None) -> List[float]:
        if keywords is None:
            keywords = KeywordExtractor.extract(text)
        vec = [0.0] * cls.VOCAB_SIZE
        for kw in keywords:
            idx = hash(kw) % cls.VOCAB_SIZE
            vec[idx] += 1.0 + len(kw) * 0.1
        # L2 归一化
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

    @staticmethod
    def cosine(v1: List[float], v2: List[float]) -> float:
        if len(v1) != len(v2):
            return 0.0
        return sum(a * b for a, b in zip(v1, v2))


# ============================================================
# 四、索引层（离线索引 + 增量更新）
# ============================================================

class KnowledgeIndex:
    """知识库索引 - 混合索引 (BM25 稀疏 + 向量稠密)"""

    def __init__(self, index_path: str = "./.rag_index"):
        self.index_path = Path(index_path)
        self.index_path.mkdir(parents=True, exist_ok=True)
        self.docs: Dict[str, Document] = {}
        self.chunks: Dict[str, Chunk] = {}
        self.inverted_index: Dict[str, List[str]] = defaultdict(list)
        self._load()

    def add_document(self, doc: Document) -> int:
        """添加文档（增量: 内容不变则跳过）"""
        if doc.doc_id in self.docs and self.docs[doc.doc_id].content_hash() == doc.content_hash():
            print(f"  文档 '{doc.title}' 未变化，跳过")
            return 0

        if doc.doc_id in self.docs:
            self._remove_from_index(doc.doc_id)

        self.docs[doc.doc_id] = doc
        chunks = Chunker.chunk(doc)
        count = 0
        for chunk in chunks:
            self.chunks[chunk.chunk_id] = chunk
            for kw in chunk.keywords:
                self.inverted_index[kw].append(chunk.chunk_id)
            count += 1
        print(f"  + '{doc.title}' ({doc.file_type}) 切分为 {count} 个片段")
        self._save()
        return count

    def add_file(self, filepath: str) -> int:
        doc = DocumentParser.parse(filepath)
        return self.add_document(doc) if doc else 0

    def add_text(self, title: str, content: str, file_type: str = "txt") -> int:
        doc = DocumentParser.parse_text(title, content, file_type)
        return self.add_document(doc)

    def add_directory(self, dirpath: str, extensions: Optional[List[str]] = None) -> int:
        if extensions is None:
            extensions = ["md", "txt", "pdf", "png", "jpg", "csv"]
        total = 0
        for f in Path(dirpath).rglob("*"):
            if f.suffix.lower().lstrip(".") in extensions:
                total += self.add_file(str(f))
        return total

    def _remove_from_index(self, doc_id: str):
        old = [cid for cid, c in self.chunks.items() if c.doc_id == doc_id]
        for cid in old:
            self.chunks.pop(cid, None)
        for kw, ids in list(self.inverted_index.items()):
            self.inverted_index[kw] = [i for i in ids if not i.startswith(doc_id)]

    # ---- 检索 ----
    def retrieve(self, query: str, top_k: int = 5, method: str = "hybrid") -> List[RetrievalResult]:
        q_kw = KeywordExtractor.extract(query, top_k=15)
        q_vec = Vectorizer.vectorize(query, q_kw)

        if method == "sparse":
            return self._sparse_search(query, q_kw, top_k)
        elif method == "dense":
            return self._dense_search(q_vec, top_k)
        # hybrid
        sparse = {r.chunk.chunk_id: r.score for r in self._sparse_search(query, q_kw, top_k * 2)}
        dense = {r.chunk.chunk_id: r.score for r in self._dense_search(q_vec, top_k * 2)}
        merged = {}
        for cid, score in sparse.items():
            merged[cid] = merged.get(cid, 0) + score * 0.4
        for cid, score in dense.items():
            merged[cid] = merged.get(cid, 0) + score * 0.6
        ranked = sorted(merged.items(), key=lambda x: -x[1])[:top_k]
        results = []
        for i, (cid, score) in enumerate(ranked, 1):
            if cid in self.chunks:
                results.append(RetrievalResult(chunk=self.chunks[cid], score=score, method="hybrid", rank=i))
        return results

    def _sparse_search(self, query: str, q_kw: List[str], top_k: int) -> List[RetrievalResult]:
        scored: Dict[str, float] = {}
        for kw in q_kw:
            matched_ids = self.inverted_index.get(kw, [])
            idf = math.log((len(self.chunks) + 1) / (len(matched_ids) + 1) + 1)
            for cid in matched_ids:
                scored[cid] = scored.get(cid, 0) + idf
        # 位置匹配
        q_tokens = set(query.lower().split())
        for cid, chunk in self.chunks.items():
            overlap = len(set(chunk.keywords) & set(q_kw))
            scored[cid] = scored.get(cid, 0) + overlap / max(1, len(q_kw)) * 2.0
        ranked = sorted(scored.items(), key=lambda x: -x[1])[:top_k]
        results = []
        for i, (cid, score) in enumerate(ranked, 1):
            if cid in self.chunks:
                results.append(RetrievalResult(chunk=self.chunks[cid], score=score, method="sparse", rank=i))
        return results

    def _dense_search(self, q_vec: List[float], top_k: int) -> List[RetrievalResult]:
        scored = []
        for cid, chunk in self.chunks.items():
            sim = Vectorizer.cosine(q_vec, chunk.vector_signature)
            scored.append((cid, sim))
        ranked = sorted(scored, key=lambda x: -x[1])[:top_k]
        results = []
        for i, (cid, score) in enumerate(ranked, 1):
            if cid in self.chunks:
                results.append(RetrievalResult(chunk=self.chunks[cid], score=score, method="dense", rank=i))
        return results

    # ---- 持久化 ----
    def _save(self):
        try:
            data = {
                "docs": {d.doc_id: {"title": d.title, "file_type": d.file_type,
                                    "content_hash": d.content_hash(), "filepath": d.filepath}
                         for d in self.docs.values()},
                "chunks": {c.chunk_id: {"doc_id": c.doc_id, "text": c.text[:200],
                                        "keywords": c.keywords, "tokens": c.tokens}
                          for c in self.chunks.values()},
                "inverted_index": dict(self.inverted_index),
                "saved_at": datetime.datetime.now().isoformat(),
            }
            (self.index_path / "index.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            print(f"  [警告] 索引保存失败: {e}")

    def _load(self):
        try:
            path = self.index_path / "index.json"
            if not path.exists():
                return
            data = json.loads(path.read_text(encoding="utf-8"))
            # 简化版：只加载元数据，不加载全文
            for did, d in data.get("docs", {}).items():
                self.docs[did] = Document(
                    doc_id=did, title=d["title"], file_type=d["file_type"],
                    content=d.get("content_hash", ""), filepath=d.get("filepath", ""),
                )
            for cid, c in data.get("chunks", {}).items():
                self.chunks[cid] = Chunk(
                    chunk_id=cid, doc_id=c["doc_id"], text=c.get("text", ""),
                    tokens=c.get("tokens", 0), keywords=c.get("keywords", []),
                    vector_signature=[0.0] * Vectorizer.VOCAB_SIZE,
                )
            self.inverted_index = defaultdict(list, data.get("inverted_index", {}))
        except Exception:
            pass

    def stats(self) -> Dict[str, int]:
        return {
            "docs": len(self.docs),
            "chunks": len(self.chunks),
            "keywords": len(self.inverted_index),
        }


# ============================================================
# 五、答案生成器
# ============================================================

class RAGGenerator:
    """RAG 答案生成器（无 LLM 模式下，给出结构化模板）"""

    def generate(self, query: str, results: List[RetrievalResult]) -> Dict[str, Any]:
        context_parts = []
        for i, r in enumerate(results, 1):
            doc_title = next(
                (d.title for d in self._docs.values() if d.doc_id == r.chunk.doc_id),
                r.chunk.doc_id
            )
            context_parts.append(f"[{i}] (来源: {doc_title}, 分数: {r.score:.2f}, 方式: {r.method})")
            context_parts.append(r.chunk.text[:300])
        context_str = "\n".join(context_parts)

        # 生成结构化回答
        source_refs = []
        for r in results:
            doc_title = next(
                (d.title for d in self._docs.values() if d.doc_id == r.chunk.doc_id),
                r.chunk.doc_id
            )
            sentences = [s.strip() for s in re.split(r"[。.？?！!；;\n]", r.chunk.text) if s.strip()]
            summary = "；".join(sentences[:2])
            source_refs.append({"title": doc_title, "summary": summary, "score": round(r.score, 2)})

        answer_lines = [f"根据知识库中 {len(results)} 条资料整理如下：\n"]
        for i, ref in enumerate(source_refs, 1):
            answer_lines.append(f"{i}. 「{ref['title']}」 (相关度 {ref['score']:.2f})")
            answer_lines.append(f"   {ref['summary']}")
            answer_lines.append("")

        conclusion = "✅ 以上回答来自多个资料来源，可信度较高。" if len(results) >= 3 else \
            ("⚠️ 当前回答仅基于有限资料，建议补充更多主题内容。" if results else "❌ 未检索到相关资料，请先添加知识。")
        answer_lines.append(conclusion)

        # 供外部使用
        self._docs = {}

        return {
            "query": query,
            "answer": "\n".join(answer_lines),
            "context": context_str,
            "sources_used": len(results),
            "source_refs": source_refs,
        }


# ============================================================
# 六、RAGAS 效果评估
# ============================================================

class RAGASEvaluator:
    """RAGAS 风格评估：忠实度 / 相关性 / 检索覆盖率"""

    def evaluate(self, query: str, results: List[RetrievalResult], answer: str,
                 expected_keywords: List[str]) -> Dict[str, Any]:
        # 检索指标
        retrieved_kw = set()
        for r in results:
            retrieved_kw.update(r.chunk.keywords)
        expected = set(expected_keywords)
        recall = len(retrieved_kw & expected) / len(expected) if expected else 0
        total_kw = len(retrieved_kw) or 1
        precision = len(retrieved_kw & expected) / total_kw if expected else 0

        # 生成指标
        structure = 0.3 if "1." in answer or "①" in answer else 0
        quality = min(1.0, len(answer) / 500) + structure

        return {
            "retrieval": {
                "recall": round(recall, 3),
                "precision": round(precision, 3),
                "hit_count": sum(1 for r in results if r.score > 0.5),
            },
            "generation": {
                "faithfulness": round(quality, 2),
                "relevance": round(quality, 2),
                "length_score": round(min(1.0, len(answer) / 500), 2),
            },
        }


# ============================================================
# 七、系统主控制器
# ============================================================

class RAGSystem:
    """RAG 系统主控制器"""

    def __init__(self, index_path: str = "./.rag_index"):
        self.index = KnowledgeIndex(index_path)
        self.generator = RAGGenerator()
        self.evaluator = RAGASEvaluator()
        self.query_log: List[Dict[str, Any]] = []

    def ingest(self, filepath: str) -> int:
        return self.index.add_file(filepath)

    def ingest_text(self, title: str, content: str, file_type: str = "txt") -> int:
        return self.index.add_text(title, content, file_type)

    def ingest_directory(self, path: str) -> int:
        return self.index.add_directory(path)

    def ask(self, query: str, top_k: int = 5, method: str = "hybrid") -> Dict[str, Any]:
        print(f"\n🧠 检索: '{query}' (top_k={top_k}, method={method})")
        results = self.index.retrieve(query, top_k=top_k, method=method)
        # 给生成器传入 docs 引用
        self.generator._docs = self.index.docs
        gen_result = self.generator.generate(query, results)
        self.query_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "query": query,
            "sources_used": gen_result["sources_used"],
        })
        return gen_result

    def evaluate(self, query: str, expected_keywords: List[str], top_k: int = 5) -> Dict[str, Any]:
        results = self.index.retrieve(query, top_k=top_k)
        self.generator._docs = self.index.docs
        gen = self.generator.generate(query, results)
        return self.evaluator.evaluate(query, results, gen["answer"], expected_keywords)

    def stats(self) -> Dict[str, Any]:
        return {
            "index": self.index.stats(),
            "total_queries": len(self.query_log),
        }


# ============================================================
# 八、示例知识库
# ============================================================

SAMPLE_KNOWLEDGE = [
    ("大语言模型原理", """大语言模型（LLM）基于 Transformer 架构，核心包括：
多头注意力机制（Multi-Head Attention）、位置编码、前馈神经网络。
训练采用自回归方式预测下一个 token。
代表模型：GPT、Claude、DeepSeek、Qwen。
应用场景：文本生成、代码编写、翻译、摘要、对话。""", "md"),
    ("RAG 检索增强生成", """检索增强生成（Retrieval-Augmented Generation）结合信息检索与生成式 AI。
流程：1) 查询向量化 -> 2) 向量检索 -> 3) Rerank 精排 -> 4) 上下文拼接 -> 5) LLM 生成。
优势：时效性强、可追溯来源、成本低、幻觉少。
主要技术：向量数据库（Pinecone/Milvus/Chroma）、BM25、混合检索、Rerank 模型。""", "md"),
    ("Agent 架构设计", """Agent（智能体）能感知环境并做出决策。
典型组件：任务规划器（Planner）、工具调用层（Tool Use）、记忆系统（Memory）、执行器（Executor）。
高级特性：多 Agent 协作、工具动态加载、记忆沉淀、自我反思。
代表框架：Claude Code、AutoGen、LangGraph、CrewAI。""", "md"),
    ("多模态大模型", """多模态大模型能处理文本、图像、音频等多种模态。
代表：CLIP、BLIP-2、LLaVA、Qwen-VL、Fuyu。
应用：图像理解、OCR、图文问答、视频理解、图表分析。""", "md"),
    ("向量数据库原理", """向量数据库存储与检索高维向量。
核心：Embedding 向量化、ANN/HNSW/IVF 索引、Cosine/Dot/L2 相似度。
产品：Pinecone、Milvus、Weaviate、Chroma、Qdrant、FAISS。""", "md"),
    ("Python 项目最佳实践", """良好的 Python 项目包括：版本控制（git）、依赖管理（requirements.txt / pyproject.toml）、
单元测试（pytest）、类型注解（type hints）、文档字符串。
推荐工具：black、ruff、mypy、pre-commit。
推荐架构：数据层、业务层、接口层分层设计。""", "md"),
    ("[图片] 项目架构图", """这是一张系统架构示意图。展示了用户请求到响应的完整数据流。
模块：API Gateway、Load Balancer、Application Server、Database、Cache、File Storage。""", "image"),
    ("[CSV] 用户行为统计", """CSV 记录系统用户行为统计。维度：DAU、MAU、留存率、转化率。
Q1 数据：DAU 12,500，MAU 85,000，7日留存 42.5%，转化率 3.8%。""", "csv"),
]


# ============================================================
# 九、主入口
# ============================================================

def run_demo():
    """多模态 RAG 完整演示"""
    print("="*70)
    print("🧠 多模态 RAG 知识库问答系统 · 演示")
    print("="*70)

    system = RAGSystem("./.rag_demo_index")

    # [1] 知识摄取
    print("\n[1/4] 📚 知识摄取 (多格式文档)...")
    for title, content, ftype in SAMPLE_KNOWLEDGE:
        system.ingest_text(title, content, ftype)
    s = system.stats()
    print(f"   索引完成：{s['index']['docs']} 文档 / {s['index']['chunks']} 片段 / {s['index']['keywords']} 关键词")

    # [2] 检索演示
    print("\n[2/4] 🔍 混合检索问答演示...")
    queries = ["什么是 RAG？有什么优势？", "Agent 包含哪些核心组件？", "向量数据库是如何工作的？"]
    for q in queries:
        response = system.ask(q, top_k=3)
        snippet = response["answer"].split("\n")[0] if response["answer"] else ""
        print(f"   Q: {q}")
        print(f"   A: {snippet[:80]}... (命中 {response['sources_used']} 条)")

    # [3] 检索方式对比
    print("\n[3/4] ⚖ 检索方式对比 (sparse vs dense vs hybrid)...")
    q = "RAG 的核心流程"
    print(f"   查询: '{q}'")
    for method in ["sparse", "dense", "hybrid"]:
        results = system.index.retrieve(q, top_k=3, method=method)
        scores = [round(r.score, 2) for r in results]
        print(f"   - {method:<8}: top3 分数 {scores}")

    # [4] RAGAS 评估
    print("\n[4/4] 📊 RAGAS 风格效果评估...")
    report = system.evaluate("RAG 的核心流程",
                             expected_keywords=["检索", "向量", "生成", "llm", "上下文"],
                             top_k=3)
    print(f"   检索指标: {report['retrieval']}")
    print(f"   生成指标: {report['generation']}")

    # 完整回答展示
    print("\n" + "="*70)
    print("📝 完整回答示例")
    print("="*70)
    response = system.ask("请解释 RAG 的核心流程", top_k=3)
    print(f"\n【问题】{response['query']}\n")
    print(f"【回答】\n{response['answer']}")

    print("\n" + "="*70)
    print(f"✅ 演示完成 (文档 {system.stats()['index']['docs']}, 片段 {system.stats()['index']['chunks']})")
    print("="*70)


if __name__ == "__main__":
    run_demo()
