#该份学生消费数据是通过自制模拟数据而来

## 📋 项目概述

本项目对消费数据进行清洗、统计和可视化分析

## 🛠️ 技术栈

- Python 3.x
- Pandas（数据处理）
- Matplotlib/Seaborn（数据可视化）


## 📊 数据结构

 字段  说明 
------------
 年级  大一、大二、大三、大四 
 学号  S001-S060 
 性别  男、女 
 餐饮支出  每月餐饮支出金额 
 娱乐支出  每月娱乐支出金额 
 其它支出  每月其它支出金额 
 月总支出  每月总支出金额 

### 环境要求

```bash
pip install -r requirements.txt
```
### 运行分析

```bash
python src/clean_student.py
```

### 查看结果

```bash
python src/show_clean_student.py
```
## 📈 分析结果

### 主要发现

1. **年级消费差异**：消费水平随年级增长呈上升趋势
2. **消费结构**：餐饮支出占比最高（约64%），娱乐支出其次（约21%）
3. **性别差异**：不同性别在各消费类别上存在差异

### 统计数据

- 有效样本：54份
- 最大月支出：XXX元
- 最小月支出：XXX元
- 平均月支出：XXX元

## 📁 项目文件说明

    文件                             说明 

 `data/student.csv`                 原始数据文件 
 `src/clean_student.py`             数据清洗、去重、异常值处理及统计分析   
 `src/show_clean_student.py`        结果展示脚本 
 `docs/作品报告.md`                 详细分析报告 

## 📄 许可证

本项目采用 [MIT License](LICENSE)。