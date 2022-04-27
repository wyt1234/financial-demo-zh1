import chinese2digits as c2d

#混合提取
print(c2d.takeNumberFromString('啊啦啦啦300十万你好我20万.3%万你好啊300咯咯咯-.34%啦啦啦300万'))
print(c2d.takeChineseNumberFromString('负百分之点二八你好啊百分之三五是不是点伍零百分之负六十五点二八'))

#将百分比转为小数
print(c2d.takeDigitsNumberFromString('234%lalalal-%nidaye+2.34%',percentConvert=True))
#案例

{'inputText': '啊啦啦啦300十万你好我20万.3%万你好啊300咯咯咯-.34%啦啦啦300万', 'replacedText': '啊啦啦啦300.0.0100000.0你好我200000.030.0你好啊300.0.0咯咯咯-0.0034啦啦啦300.0.00000.0', 'CHNumberStringList': ['300', '十万', '20万', '.3%万', '300', '-.34%', '300万'], 'digitsStringList': ['300.0', '100000.0', '200000.0', '30.0', '300.0', '-0.0034', '3000000.0']}

{'inputText': '234%lalalal-%nidaye+2.34%', 'digitsNumberStringList': ['2.34', '0.0234']}

{'inputText': '百分之四百三十二万分之四三千分之五', 'replacedText': '4.320.00430.005', 'CHNumberStringList': ['百分之四百三十二', '万分之四三', '千分之五'], 'digitsStringList': ['4.32', '0.0043', '0.005']}

{'inputText': '伍亿柒仟万拾柒今天天气不错百分之三亿二百万五啦啦啦啦负百分之点二八你好啊三万二', 'replacedText': '570000017今天天气不错3020050.0啦啦啦啦-0.0028你好啊32000', 'CHNumberStringList': ['五亿七千万十七', '百分之三亿二百万五', '负百分之点二八', '三万二'], 'digitsStringList': ['570000017', '3020050.0', '-0.0028', '32000']}

{'inputText': 'llalala万三威风威风千四五', 'replacedText': 'llalala0.0003威风威风0.045', 'CHNumberStringList': ['万三', '千四五'], 'digitsStringList': ['0.0003', '0.045']}

{'inputText': '哥两好', 'replacedText': '哥两好', 'CHNumberStringList': [], 'digitsStringList': []}

{'inputText': '伍亿柒仟万拾柒百分之', 'replacedText': '570000017百分之', 'CHNumberStringList': ['五亿七千万十七'], 'digitsStringList': ['570000017']}

{'inputText': '负百分之点二八你好啊百分之三五是不是点五零百分之负六十五点二八', 'replacedText': '-0.0028你好啊0.35是不是0.50-0.6528', 'CHNumberStringList': ['负百分之点二八', '百分之三五', '点五零', '百分之负六十五点二八'], 'digitsStringList': ['-0.0028', '0.35', '0.50', '-0.6528']}