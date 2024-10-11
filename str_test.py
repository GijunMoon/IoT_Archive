a = '외부습도/외부온도/실내습도/실내온도/조도/비/pm2.5/실외불쾌지수/실내불쾌지수/실내불쾌지수 상태'

line = a.split('/')
for i in line:
    print(i)

print(line[0])