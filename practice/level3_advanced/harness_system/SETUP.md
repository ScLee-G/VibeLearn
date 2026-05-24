# Harness 系统完整前置准备清单

本指南列出运行 Harness 系统的所有必要前置条件，请确保所有条件满足后再开始使用。

---

## 📋 前置准备清单（按重要性排序）

### 🔴 必需项目（不满足无法运行）

#### 1. Python 环境
- **要求**: Python 3.8 或更高版本
- **推荐**: Python 3.10 或 3.11
- **验证命令**:
  ```bash
  python --version
  # 或
  python3 --version
  ```

#### 2. 网络连接
- **要求**: 可访问公网
- **验证**: 能访问网站如 Google, Github 等
- **可能需要代理**: 视地区而定

#### 3. OpenAI API Key
- **要求**: 有效的 OpenAI API Key（或兼容 API 密钥）
- **获取地址**: https://platform.openai.com/api-keys
- **设置方式**:
  ```bash
  # Linux/Mac
  export OPENAI_API_KEY="sk-xxxxxxxxxxxx"

  # Windows
  set OPENAI_API_KEY=sk-xxxxxxxxxxxx
  ```

#### 4. 必需 Python 包
- **要求**: 安装 openai 包
- **安装命令**:
  ```bash
  pip install openai
  ```

#### 5. 系统资源最低要求
- **内存**: 2 GB RAM
- **磁盘**: 500 MB 可用空间
- **CPU**: 1 核心以上

---

### 🟡 强烈推荐（缺少可能影响性能）

#### 6. 推荐系统配置
- **内存**: 8 GB RAM 或更多
- **磁盘**: 2 GB 可用空间
- **CPU**: 4 核心或更多

#### 7. 资源监控依赖
- **要求**: psutil 包
- **安装**:
  ```bash
  pip install psutil
  ```

#### 8. API 基础 URL
- **可选，但方便配置**:
  ```bash
  # 推荐设置以防默认地址访问慢
  export OPENAI_BASE_URL="https://api.openai.com/v1"
  ```

#### 9. 其他工具依赖
- **可选**: pandas（如果处理数据任务）
  ```bash
  pip install pandas
  ```

---

### 🟢 可选（锦上添花）

#### 10. IDE 或文本编辑器
- 推荐使用 VSCode, PyCharm 等

#### 11. Git（推荐用于版本管理）

#### 12. 虚拟环境（推荐避免冲突）
- 使用 venv 或 conda

---

## 🚀 快速开始完整流程

### 第一步：系统检查（推荐）

```bash
cd /workspace/practice/level3_advanced/harness_system
python precheck.py
```

### 第二步：如果检查失败，先修复问题

### 第三步：运行 Harness 系统

```bash
# 自动检查后运行
python run_harness.py "你的任务描述"

# 或者独立运行检查
python precheck.py
python run_harness.py "任务"
```

---

## ⚙️ 完整环境配置步骤

### 1. 检查 Python 版本

```bash
python --version
```

如果不是 3.8+，请先升级 Python。

### 2. 创建虚拟环境（推荐）

```bash
python -m venv venv

# 激活环境
# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 设置 API 密钥

```bash
# Linux/Mac
export OPENAI_API_KEY="你的API_KEY"
export OPENAI_BASE_URL="https://api.openai.com/v1"  # 可选

# Windows
set OPENAI_API_KEY=你的API_KEY
set OPENAI_BASE_URL=https://api.openai.com/v1
```

### 5. 运行完整检查

```bash
python precheck.py
```

---

## ❓ 常见问题解决

### 问题：Python 版本过低
**解决**: 下载并安装 Python 3.10+

### 问题：缺少 API 密钥
**解决**: 从 https://platform.openai.com/api-keys 获取

### 问题：API 连接失败
**解决**:
1. 检查网络
2. 可能需要配置代理
3. 确认 API 密钥是否正确

### 问题：内存不足
**解决**:
1. 关闭其他程序
2. 增加虚拟内存（swap 空间）
3. 使用 --no-resource-monitor 选项

### 问题：磁盘空间不足
**解决**:
1. 清理临时文件
2. 删除不需要的文件

---

## 📊 检查项目详细说明

| 检查项 | 状态 | 说明 | 失败怎么办 |
|--------|------|------|-----------|
| Python 版本 | 必需 | <3.8 不行 | 升级 Python |
| 内存 | 推荐/警告 | <2GB 警告，<1.5GB 危险 | 关闭程序，加内存 |
| CPU | 必需 | <1核心不行 | 换电脑或使用云 |
| 磁盘 | 必需 | <500MB不行 | 清理磁盘 |
| 网络连接 | 必需 | 无公网不行 | 检查网络连接 |
| openai包 | 必需 | 必须安装 | pip install openai |
| psutil包 | 推荐 | 建议安装 | pip install psutil |
| API密钥 | 必需 | 必须有 | 去OpenAI网站获取 |
| API连通性 | 测试 | 验证连接 | 检查网络和密钥 |
| 文件系统 | 必需 | 读写权限 | 检查当前目录权限 |

---

## 📁 项目目录权限要求

确保以下目录具有读写权限：
- 项目根目录
- 临时目录（系统）

---

## ⏭️ 完成准备后

所有准备工作完成后，运行:

```bash
python precheck.py  # 再次确认
python run_harness.py "你的第一个任务"
```

祝你使用愉快！ 🎉
