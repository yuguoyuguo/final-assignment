# -*- coding: utf-8 -*-
import pandas as pd



df = pd.read_csv('data/student.csv')

'''
清洗
'''
print(f'*形状：{df.shape}')
print(f'*缺失值：\n{df.isnull().sum()}')
df = df.dropna(axis=0, how='any')#axis=0：按行执行 how=any：所有含空值
print(f"*已删除缺失值")

#                         全列匹配整行重复
duplicate = df.duplicated(subset=None).sum()
print(f"\n*重复量：{duplicate}")
if duplicate >= 1:
    df = df.drop_duplicates(subset=None)
    

abnormal = df[(df['餐饮支出'] < 0) | (df['娱乐支出'] < 0) | (df['其它支出'] < 0) | (df['月总支出'] < 0)]
print(f"*异常值：{abnormal}")
df = df.drop(abnormal.index)
print(f"*已删除异常值\n")


df['计算总支出'] = df['餐饮支出'] + df['娱乐支出'] + df['其它支出']
no_equality = df[df['月总支出'] != df['计算总支出']]
print(f"*支出总计算不同：{len(no_equality)}条")

df = df.drop(no_equality.index)
df = df.drop("计算总支出", axis=1)

df.to_csv('data/clean_student.csv')




'''
分析
'''

gender = df.groupby('性别')[['餐饮支出', '娱乐支出', '其它支出', '月总支出']].mean().round(2)
print(gender)
grade = df.groupby('年级')[['餐饮支出', '娱乐支出', '其它支出', '月总支出']].mean().round(2)
print(grade)


food = df['餐饮支出'].sum()
entertainment = df['娱乐支出'].sum()
study = df['其它支出'].sum()
all = food + entertainment + study


print(f"餐饮：{food / all * 100:.2f}%")
print(f"娱乐：{entertainment / all * 100:.2f}%")
print(f"其它：{study / all * 100:.2f}%")

grade_gender_stats = df.groupby(['年级', '性别'])[['月总支出', '餐饮支出', '娱乐支出']].mean().round(2)
print("分年级性别消费统计：")
print(grade_gender_stats)

top5 = df.nlargest(5, '月总支出')[['学号', '年级', '性别', '餐饮支出', '娱乐支出', '其它支出', '月总支出']]
bottom5 = df.nsmallest(5, '月总支出')[['学号', '年级', '性别', '餐饮支出', '娱乐支出', '其它支出', '月总支出']]

print("消费TOP5学生：")
print(top5)
print("\n消费垫底TOP5学生：")
print(bottom5)

print(f"{df['月总支出'].max()}元")
print(f"{df['月总支出'].min()}元")
print(f"{df['月总支出'].mean():.2f}元","\n")