# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
# 字体设置
plt.rcParams['font.sans-serif'] = ['SimHei']

df = pd.read_csv('data/clean_student.csv')

#柱状图计算 #groupby；分组 #.loc；定位索引
grades = ['大一', '大二', '大三', '大四']
grade_stats = df.groupby('年级')[['月总支出']].sum()
total = [grade_stats.loc[g, '月总支出'] for g in grades]

#饼图计算
food = df['餐饮支出'].sum()
entertainment = df['娱乐支出'].sum()
study = df['其它支出'].sum()


# 柱状图
plt.figure(figsize=(10,6))
plt.bar(grades, total)
plt.title('年级月总支出对比')
plt.xlabel('年级')
plt.ylabel('支出总金额')
plt.legend(['月总支出'])

#饼图
plt.figure(figsize=(10,6))
plt.pie([food, entertainment, study], labels=['餐饮支出', '娱乐支出', '其它支出'], autopct='%1.1f%%')
plt.title('月支出比例')
#颜色区分
plt.legend()

plt.show()