import cn2an

# 在 strict 模式（默认）下，只有严格符合数字拼写的才可以进行转化
output = cn2an.cn2an("一百二十三")
# 或者
output = cn2an.cn2an("一百二十三", "strict")
# output:
# 123

# 在 normal 模式下，可以将 一二三 进行转化
output = cn2an.cn2an("一二三", "normal")
# output:
# 123

# 在 smart 模式下，可以将混合拼写的 1百23 进行转化
output = cn2an.cn2an("1百23", "smart")
# output:
# 123

# 以上三种模式均支持负数
output = cn2an.cn2an("负一百二十三", "strict")
# output:
# -123

# 以上三种模式均支持小数
output = cn2an.cn2an("一点二三", "strict")
# output

# 在 cn2an 方法（默认）下，可以将句子中的中文数字转成阿拉伯数字
output = cn2an.transform("小王捡了一百块钱")
# 或者
output = cn2an.transform("小王捡了一百块钱", "cn2an")
# output:
# 小王捡了100块钱

# 在 an2cn 方法下，可以将句子中的中文数字转成阿拉伯数字
output = cn2an.transform("小王捡了100块钱", "an2cn")
output = cn2an.transform("小王捡了100块钱", "cn2an")
# output:
# 小王捡了一百块钱


## 支持日期
output = cn2an.transform("小王的生日是二零零一年三月四日", "cn2an")
# output:
# 小王的生日是2001年3月4日

output = cn2an.transform("小王的生日是2001年3月4日", "an2cn")
# output:
# 小王的生日是二零零一年三月四日

## 支持分数
output = cn2an.transform("抛出去的硬币为正面的概率是二分之一", "cn2an")
# output:
# 抛出去的硬币为正面的概率是1/2

output = cn2an.transform("抛出去的硬币为正面的概率是1/2", "an2cn")
# output:
# 抛出去的硬币为正面的概率是二分之一

## 支持百分比
## 支持摄氏度